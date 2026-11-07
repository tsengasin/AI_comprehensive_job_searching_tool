"""Progress report: turn your job search into a visible improvement loop.

Job searching feels like failure most of the time: you only hear back from a few
applications, and rejections rarely say why. This report shows what you control
and what is improving, week by week:

- outcomes: applications, interviews, interview rate
- CV quality: average ATS Match % of your strong-fit jobs (rises as you fix wording)
- effort: tailored CVs and mock interviews you completed
- focus: the CV terms and skill gaps that come up most, so next week has a clear target

You update the "Status" column in data/jobs.xlsx (New, Applied, Interview, Offer,
Rejected, No reply, Not applying). Each run records when a status changed, so the
report can show your timeline without you typing dates.
"""

from __future__ import annotations

import html
import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, timedelta

from .config import DATA_DIR, MY_DATA_DIR, Config
from . import store

HISTORY_FILE = DATA_DIR / "status_history.json"
REPORT_FILE = DATA_DIR / "progress-report.html"

STATUSES = ["New", "Applied", "Interview", "Offer", "Rejected", "No reply", "Not applying"]
APPLIED_OR_LATER = {"applied", "interview", "offer", "rejected", "no reply"}
INTERVIEW_OR_LATER = {"interview", "offer"}
MIN_APPLICATIONS_FOR_RATE = 5
_DATE_IN_NAME = re.compile(r"(\d{4}-\d{2}-\d{2})")


# --- status history -------------------------------------------------------

def update_history(rows: list[dict], today: date | None = None) -> dict:
    """Record the first date each job reached each status. Returns the history."""
    today_s = (today or date.today()).isoformat()
    history = json.loads(HISTORY_FILE.read_text(encoding="utf-8")) if HISTORY_FILE.exists() else {}
    for row in rows:
        job_id = str(row.get("Job ID") or "")
        status = str(row.get("Status") or "New").strip().lower()
        if not job_id:
            continue
        seen = history.setdefault(job_id, {})
        if status not in seen:
            # The first time we see a job it may already be past "new"; fall back
            # to the date it was found so old rows still land in a sensible week.
            seen[status] = today_s if seen else str(row.get("Date Found") or today_s)[:10]
    store.ensure_data_dir()
    HISTORY_FILE.write_text(json.dumps(history, indent=1), encoding="utf-8")
    return history


def _first_date(history_entry: dict, statuses: set[str]) -> str | None:
    dates = [d for s, d in history_entry.items() if s in statuses]
    return min(dates) if dates else None


# --- metrics --------------------------------------------------------------

def week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


@dataclass
class Week:
    start: date
    found: int = 0
    strong: int = 0
    applied: int = 0
    interviews: int = 0
    ats_values: list[int] = field(default_factory=list)
    tailored: int = 0
    mocks: int = 0

    @property
    def avg_ats(self) -> float | None:
        return sum(self.ats_values) / len(self.ats_values) if self.ats_values else None


def _dated_files(pattern: str) -> list[date]:
    out = []
    for path in MY_DATA_DIR.glob(pattern):
        m = _DATE_IN_NAME.search(path.name)
        if m:
            try:
                out.append(date.fromisoformat(m.group(1)))
            except ValueError:
                pass
    return out


def build_weeks(rows: list[dict], history: dict, config: Config, weeks: int = 12,
                today: date | None = None) -> list[Week]:
    today = today or date.today()
    first = week_start(today) - timedelta(weeks=weeks - 1)
    table = {first + timedelta(weeks=i): Week(first + timedelta(weeks=i)) for i in range(weeks)}

    def bucket(day: str | date | None) -> Week | None:
        if not day:
            return None
        d = day if isinstance(day, date) else date.fromisoformat(str(day)[:10])
        return table.get(week_start(d))

    for row in rows:
        found = bucket(row.get("Date Found"))
        fit = row.get("Fit %") or 0
        if found:
            found.found += 1
            if fit >= config.thresholds.alert_min_fit:
                found.strong += 1
                if row.get("ATS %") is not None:
                    found.ats_values.append(int(row["ATS %"]))
        entry = history.get(str(row.get("Job ID") or ""), {})
        applied = bucket(_first_date(entry, APPLIED_OR_LATER))
        if applied:
            applied.applied += 1
        interview = bucket(_first_date(entry, INTERVIEW_OR_LATER))
        if interview:
            interview.interviews += 1

    for d in _dated_files("tailored/*"):
        if (w := bucket(d)):
            w.tailored += 1
    for d in _dated_files("interview-prep/*/04_practice_log/*.md"):
        if (w := bucket(d)):
            w.mocks += 1
    return [table[k] for k in sorted(table)]


def _rate(interviews: int, applied: int) -> float | None:
    return interviews / applied * 100 if applied else None


def summarise(weeks: list[Week], rows: list[dict], history: dict, config: Config) -> dict:
    recent, previous = weeks[-4:], weeks[-8:-4]

    def total(ws, attr):
        return sum(getattr(w, attr) for w in ws)

    def avg_ats(ws):
        vals = [v for w in ws for v in w.ats_values]
        return sum(vals) / len(vals) if vals else None

    # Cumulative interview rate over everything you have applied to.
    applied_all = sum(1 for r in rows if _first_date(history.get(str(r.get("Job ID") or ""), {}), APPLIED_OR_LATER))
    interviews_all = sum(1 for r in rows if _first_date(history.get(str(r.get("Job ID") or ""), {}), INTERVIEW_OR_LATER))

    s = {
        "applied_recent": total(recent, "applied"),
        "applied_prev": total(previous, "applied"),
        "interviews_recent": total(recent, "interviews"),
        "rate_recent": _rate(total(recent, "interviews"), total(recent, "applied")),
        "rate_prev": _rate(total(previous, "interviews"), total(previous, "applied")),
        "rate_all": _rate(interviews_all, applied_all),
        "applied_all": applied_all,
        "interviews_all": interviews_all,
        "ats_recent": avg_ats(recent),
        "ats_prev": avg_ats(previous),
        "tailored_recent": total(recent, "tailored"),
        "mocks_recent": total(recent, "mocks"),
        "effort_prev": total(previous, "tailored") + total(previous, "mocks") + total(previous, "applied"),
        "strong_recent": total(recent, "strong"),
    }
    s["effort_recent"] = s["tailored_recent"] + s["mocks_recent"] + s["applied_recent"]

    # Focus for next week, from recent strong-fit jobs.
    cutoff = recent[0].start.isoformat()
    recent_rows = [r for r in rows if str(r.get("Date Found", ""))[:10] >= cutoff]
    terms, gaps = Counter(), Counter()
    for r in recent_rows:
        if (r.get("Fit %") or 0) >= config.thresholds.alert_min_fit:
            terms.update(t.strip().lower() for t in str(r.get("Missing ATS Terms") or "").split(",") if t.strip())
        gaps.update(g.strip() for g in str(r.get("Gap Flags") or "").split("|") if g.strip())
    s["focus_terms"] = terms.most_common(5)
    s["focus_gaps"] = gaps.most_common(3)
    return s


def _delta(now: float | None, before: float | None, unit: str) -> str:
    if now is None or before is None:
        return "no earlier data yet"
    diff = now - before
    sign = "+" if diff > 0 else ("−" if diff < 0 else "±")
    return f"{sign}{abs(diff):.0f}{unit} vs previous 4 weeks"


def text_summary(s: dict, config: Config) -> str:
    lines = ["📈 Your weekly progress (last 4 weeks)", ""]
    if s["applied_recent"] >= MIN_APPLICATIONS_FOR_RATE and s["rate_recent"] is not None:
        lines.append(f"Interview rate: {s['rate_recent']:.0f}% ({s['interviews_recent']} of {s['applied_recent']}) · "
                     + _delta(s["rate_recent"], s["rate_prev"], " pts"))
    else:
        lines.append(f"Applications: {s['applied_recent']} (interview rate shows from {MIN_APPLICATIONS_FOR_RATE})")
    if s["ats_recent"] is not None:
        lines.append(f"CV wording (avg ATS on strong-fit jobs): {s['ats_recent']:.0f}% · "
                     + _delta(s["ats_recent"], s["ats_prev"], " pts") + f" · target {config.thresholds.ats_target}%")
    lines.append(f"Effort you control: {s['applied_recent']} applications, {s['tailored_recent']} tailored CVs, "
                 f"{s['mocks_recent']} mock interviews · " + _delta(s["effort_recent"], s["effort_prev"], ""))
    if s["focus_terms"]:
        lines += ["", "Focus next week (add to CV if true): " + ", ".join(t for t, _ in s["focus_terms"][:3])]
    if s["focus_gaps"]:
        lines.append("Skill gap to work on: " + s["focus_gaps"][0][0])
    lines += ["", encouragement(s), "", "Full report: data/progress-report.html"]
    return "\n".join(lines)


def encouragement(s: dict) -> str:
    if s["rate_recent"] is not None and s["rate_prev"] is not None and s["rate_recent"] > s["rate_prev"]:
        return "Your interview rate is going up. What you changed is working: keep it."
    if s["ats_recent"] is not None and s["ats_prev"] is not None and s["ats_recent"] > s["ats_prev"]:
        return "Your CV is matching job language better than a month ago. That compounds."
    if s["effort_recent"] > s["effort_prev"]:
        return "You put in more focused effort than last month. Results lag effort by a few weeks."
    return ("Rejections are data, not a verdict. Pick one focus item above for this week; "
            "small, steady fixes are what move the numbers.")


# --- HTML report ----------------------------------------------------------

def _fmt(v: float | None, unit: str = "%") -> str:
    return "—" if v is None else f"{v:.0f}{unit}"


def _chart(title: str, subtitle: str, weeks: list[Week], values: list[float | None], kind: str,
           unit: str = "", target: float | None = None, y_max: float | None = None) -> str:
    """A single-series SVG chart (bars or line), with native hover tooltips."""
    # Small viewBox so text stays readable when the chart shrinks on a phone.
    w, h, left, right, top, bottom = 400, 210, 38, 10, 16, 28
    pw, ph = w - left - right, h - top - bottom
    known = [v for v in values if v is not None]
    vmax = y_max or _nice_max(max([*(known or [0]), target or 0, 1]))
    n = len(weeks)
    x = lambda i: left + pw * (i + 0.5) / n
    y = lambda v: top + ph * (1 - v / vmax)
    parts = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{html.escape(title)}">']
    for frac in (0, 0.5, 1):
        gy = top + ph * (1 - frac)
        parts.append(f'<line x1="{left}" x2="{w - right}" y1="{gy:.1f}" y2="{gy:.1f}" class="grid"/>')
        parts.append(f'<text x="{left - 6}" y="{gy + 4:.1f}" class="tick" text-anchor="end">{vmax * frac:.0f}{unit}</text>')
    for i, wk in enumerate(weeks):
        if i % 2 == (n - 1) % 2:
            parts.append(f'<text x="{x(i):.1f}" y="{h - 10}" class="tick" text-anchor="middle">{wk.start:%d %b}</text>')
    if target is not None:
        ty = y(target)
        parts.append(f'<line x1="{left}" x2="{w - right}" y1="{ty:.1f}" y2="{ty:.1f}" class="target"/>')
        parts.append(f'<text x="{left + 4}" y="{ty - 5:.1f}" class="tick">target {target:.0f}{unit}</text>')
    if kind == "bar":
        bw = min(22, pw / n * 0.6)
        for i, v in enumerate(values):
            label = f"Week of {weeks[i].start:%d %b}: {0 if v is None else v:.0f}{unit}"
            if v:
                by = y(v)
                bh = top + ph - by
                r = min(4, bh / 2, bw / 2)
                x0, x1, base = x(i) - bw / 2, x(i) + bw / 2, top + ph
                path = (f"M{x0:.1f},{base:.1f} V{by + r:.1f} Q{x0:.1f},{by:.1f} {x0 + r:.1f},{by:.1f} "
                        f"H{x1 - r:.1f} Q{x1:.1f},{by:.1f} {x1:.1f},{by + r:.1f} V{base:.1f} Z")
                parts.append(f'<path d="{path}" class="bar"><title>{label}</title></path>')
            parts.append(f'<rect x="{x(i) - pw / n / 2:.1f}" y="{top}" width="{pw / n:.1f}" height="{ph}" class="hit"><title>{label}</title></rect>')
    else:
        pts = [(x(i), y(v), i, v) for i, v in enumerate(values) if v is not None]
        if len(pts) > 1:
            parts.append('<polyline class="line" points="' + " ".join(f"{px:.1f},{py:.1f}" for px, py, _, _ in pts) + '"/>')
        for px, py, i, v in pts:
            label = f"Week of {weeks[i].start:%d %b}: {v:.0f}{unit}"
            parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="4.5" class="dot"><title>{label}</title></circle>')
            parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="14" class="hit"><title>{label}</title></circle>')
        if pts:
            px, py, _, v = pts[-1]
            parts.append(f'<text x="{px:.1f}" y="{py - 10:.1f}" class="value" text-anchor="middle">{v:.0f}{unit}</text>')
        else:
            parts.append(f'<text x="{w / 2}" y="{h / 2}" class="tick" text-anchor="middle">Not enough data yet</text>')
    parts.append("</svg>")
    return (f'<section class="card"><h2>{html.escape(title)}</h2><p class="sub">{html.escape(subtitle)}</p>'
            + "".join(parts) + "</section>")


def _nice_max(v: float) -> float:
    """Round an axis maximum up so the half-way gridline is a whole number."""
    for step in (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000):
        if v <= step * 2:
            return step * 2
    return v


def _tile(label: str, value: str, note: str) -> str:
    return (f'<div class="tile"><div class="label">{html.escape(label)}</div>'
            f'<div class="big">{html.escape(value)}</div><div class="note">{html.escape(note)}</div></div>')


def render_html(weeks: list[Week], s: dict, config: Config) -> str:
    t = config.thresholds
    rate_value = _fmt(s["rate_recent"]) if s["applied_recent"] >= MIN_APPLICATIONS_FOR_RATE else "—"
    rate_note = (_delta(s["rate_recent"], s["rate_prev"], " pts")
                 if rate_value != "—" else f"shows after {MIN_APPLICATIONS_FOR_RATE} applications in 4 weeks")
    tiles = "".join([
        _tile("Interview rate · last 4 weeks", rate_value, rate_note),
        _tile("Applications · last 4 weeks", str(s["applied_recent"]), _delta(s["applied_recent"], s["applied_prev"], "")),
        _tile("CV wording (avg ATS, strong-fit jobs)", _fmt(s["ats_recent"]),
              _delta(s["ats_recent"], s["ats_prev"], " pts") + f" · target {t.ats_target}%"),
        _tile("Focused effort · last 4 weeks", str(s["effort_recent"]),
              f"{s['tailored_recent']} tailored CVs · {s['mocks_recent']} mocks · {s['applied_recent']} applications"),
    ])

    rolling = []
    for i in range(len(weeks)):
        win = weeks[max(0, i - 3): i + 1]
        applied, interviews = sum(w.applied for w in win), sum(w.interviews for w in win)
        rolling.append(_rate(interviews, applied) if applied >= MIN_APPLICATIONS_FOR_RATE else None)

    charts = "".join([
        _chart("Applications per week", "Effort you control. Steady beats bursts.",
               weeks, [float(w.applied) for w in weeks], "bar"),
        _chart("Interview rate (rolling 4 weeks)",
               f"Interviews ÷ applications. Shown once a 4-week window has {MIN_APPLICATIONS_FOR_RATE}+ applications.",
               weeks, rolling, "line", unit="%", y_max=100),
        _chart("CV wording: average ATS Match % on strong-fit jobs",
               "Rises as you add true, job-language wording to your CV.",
               weeks, [w.avg_ats for w in weeks], "line", unit="%", target=t.ats_target, y_max=100),
    ])

    focus_terms = "".join(f"<li>{html.escape(term)} <span class='muted'>({n} jobs)</span></li>" for term, n in s["focus_terms"]) \
        or "<li class='muted'>No missing terms recorded yet.</li>"
    focus_gaps = "".join(f"<li>{html.escape(g)} <span class='muted'>({n})</span></li>" for g, n in s["focus_gaps"]) \
        or "<li class='muted'>No recurring gaps yet.</li>"

    table_rows = "".join(
        f"<tr><td>{w.start:%d %b %Y}</td><td>{w.found}</td><td>{w.strong}</td><td>{w.applied}</td>"
        f"<td>{w.interviews}</td><td>{_fmt(w.avg_ats)}</td><td>{w.tailored}</td><td>{w.mocks}</td></tr>"
        for w in reversed(weeks))

    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Job Search Progress</title>
<style>
:root {{ color-scheme: light; --surface:#f6f8fb; --card:#fcfcfb; --text:#0b0b0b; --text2:#52514e; --muted:#7a7974;
  --grid:#e4e3df; --series:#2a78d6; --ring:#fcfcfb; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ color-scheme: dark; --surface:#121211; --card:#1a1a19;
  --text:#f0efec; --text2:#c3c2b7; --muted:#9a998f; --grid:#383835; --series:#3987e5; --ring:#1a1a19; }} }}
:root[data-theme="dark"] {{ color-scheme: dark; --surface:#121211; --card:#1a1a19; --text:#f0efec; --text2:#c3c2b7;
  --muted:#9a998f; --grid:#383835; --series:#3987e5; --ring:#1a1a19; }}
* {{ box-sizing: border-box; }}
body {{ margin:0; background:var(--surface); color:var(--text); font:15px/1.5 Inter, system-ui, -apple-system, "Segoe UI", sans-serif; }}
main {{ max-width: 1000px; margin: 0 auto; padding: 24px 16px 48px; }}
h1 {{ font-size: 26px; margin: 0 0 4px; }} h2 {{ font-size: 16px; margin: 0; }}
.lede {{ color: var(--text2); margin: 0 0 20px; }}
.tiles {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 12px; margin-bottom: 16px; }}
.tile, .card {{ background: var(--card); border: 1px solid var(--grid); border-radius: 12px; padding: 16px; }}
.label {{ color: var(--text2); font-size: 13px; }} .big {{ font-size: 34px; font-weight: 700; margin: 2px 0; }}
.note, .sub, .muted {{ color: var(--muted); font-size: 13px; }} .sub {{ margin: 2px 0 8px; }}
.message {{ background: var(--card); border-left: 4px solid var(--series); border-radius: 8px; padding: 12px 16px; margin: 0 0 16px; }}
.grid2 {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 12px; margin: 12px 0; }}
.card {{ margin-bottom: 12px; }} .charts {{ display:grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 12px; }}
.charts .card {{ margin: 0; }} svg {{ width: 100%; height: auto; display: block; }}
svg .grid {{ stroke: var(--grid); stroke-width: 1; }} svg .target {{ stroke: var(--muted); stroke-width: 1.5; stroke-dasharray: 5 4; }}
svg .tick {{ fill: var(--muted); font-size: 12px; }} svg .value {{ fill: var(--text); font-size: 13px; font-weight: 600; }}
svg .bar {{ fill: var(--series); }} svg .line {{ fill: none; stroke: var(--series); stroke-width: 2; }}
svg .dot {{ fill: var(--series); stroke: var(--ring); stroke-width: 2; }} svg .hit {{ fill: transparent; }}
svg .bar:hover {{ opacity: .85; }}
ul {{ margin: 8px 0 0; padding-left: 20px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 13px; }} th, td {{ text-align: right; padding: 6px 8px; border-bottom: 1px solid var(--grid); }}
th:first-child, td:first-child {{ text-align: left; }} th {{ color: var(--text2); font-weight: 600; }}
.scroll {{ overflow-x: auto; }} details summary {{ cursor: pointer; font-weight: 600; }}
</style></head>
<body><main>
<h1>Your job search progress</h1>
<p class="lede">Generated {date.today():%d %b %Y}. You can't control who replies; you can control what improves. This page shows both.</p>
<p class="message">{html.escape(encouragement(s))}</p>
<div class="tiles">{tiles}</div>
<div class="charts">{charts}</div>
<div class="grid2">
  <section class="card"><h2>Focus next week: CV wording</h2><p class="sub">Missing from your CV in recent strong-fit jobs. Add only if true.</p><ul>{focus_terms}</ul></section>
  <section class="card"><h2>Focus next week: skills</h2><p class="sub">Gaps that capped your fit most often. Ask interview-coach for a study plan.</p><ul>{focus_gaps}</ul></section>
</div>
<section class="card"><details><summary>Weekly numbers (table)</summary><div class="scroll"><table>
<thead><tr><th>Week of</th><th>Jobs found</th><th>Strong fit (≥{t.alert_min_fit}%)</th><th>Applied</th><th>Interviews</th><th>Avg ATS</th><th>Tailored CVs</th><th>Mock interviews</th></tr></thead>
<tbody>{table_rows}</tbody></table></div></details></section>
<p class="muted">All-time: {s['interviews_all']} interview(s) from {s['applied_all']} application(s){f" ({s['rate_all']:.0f}%)" if s['rate_all'] is not None else ""}.
Update the Status column in data/jobs.xlsx after each application and reply; this report does the rest.</p>
</main></body></html>"""


def generate(config: Config, today: date | None = None) -> tuple[str, dict]:
    rows = store.read_tracker()
    history = update_history(rows, today)
    weeks = build_weeks(rows, history, config, today=today)
    s = summarise(weeks, rows, history, config)
    REPORT_FILE.write_text(render_html(weeks, s, config), encoding="utf-8")
    return text_summary(s, config), s
