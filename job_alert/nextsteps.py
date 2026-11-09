"""Tell the user what to do next, instead of waiting for them to ask.

Looks at where they are (setup, tracker, statuses, interview prep files) and picks the
few actions that matter most today. Each action comes with a sentence they can say to
their AI agent, so acting on it takes one step.

Used by:  python -m job_alert next   ·   the daily Telegram digest   ·   the job-search-coach skill
"""

from __future__ import annotations

import os
import re
import time
from collections import Counter
from dataclasses import dataclass
from datetime import date, timedelta

from .config import MY_DATA_DIR, ROOT, Config
from .progress import APPLIED_OR_LATER, _first_date

FRESH_DAYS = 10          # act on new matches while they are still open
FOLLOW_UP_DAYS = 21      # no answer after this long: follow up or mark "No reply"
PROFILE_STALE_DAYS = 45  # remind to refresh the skill profile


@dataclass
class Action:
    priority: int        # lower = more urgent
    title: str
    why: str
    say: str = ""        # what to say to the AI agent
    run: str = ""        # or a command to run
    link: str = ""       # or a page to open

    def text(self, n: int) -> str:
        lines = [f"{n}. {self.title}", f"   Why: {self.why}"]
        if self.say:
            lines.append(f"   Say to your AI: “{self.say}”")
        if self.run:
            lines.append(f"   Run: {self.run}")
        if self.link:
            lines.append(f"   Open: {self.link}")
        return "\n".join(lines)


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(text).lower())


def _days_since(day: str | None, today: date) -> int | None:
    if not day:
        return None
    try:
        return (today - date.fromisoformat(str(day)[:10])).days
    except ValueError:
        return None


def setup_actions(config: Config | None) -> list[Action]:
    actions = []
    if config is None:
        return [Action(1, "Finish setup: create config.yaml",
                       "The daily alert needs your job titles and location.",
                       say="Help me set up the job search tool.")]
    if not (ROOT / config.cv_file).exists():
        actions.append(Action(1, "Add your CV",
                              f"Nothing can be scored or tailored without it ({config.cv_file}).",
                              say="Use cv-builder to build my master CV."))
    if not (ROOT / config.profile_file).exists():
        actions.append(Action(2, "Build your skill profile (10 minutes)",
                              "It makes your Fit scores honest instead of keyword-inflated.",
                              say="Run skill-profile-builder."))
    keys = {"jooble": "JOOBLE_APP_KEY", "serpapi": "SERPAPI_KEY"}
    if not any(os.environ.get(keys[s]) for s in config.sources if s in keys):
        actions.append(Action(3, "Get a free job-search key (Jooble or SerpApi)",
                              "The daily alert has no job source yet.",
                              run="see docs/02-api-keys.md, then: python -m job_alert doctor"))
    return actions


def job_actions(rows: list[dict], history: dict, config: Config, today: date) -> list[Action]:
    actions: list[Action] = []
    t = config.thresholds

    def status(r):
        return str(r.get("Status") or "New").strip().lower()

    def fresh(r):
        d = _days_since(r.get("Date Found"), today)
        return d is not None and d <= FRESH_DAYS

    # Interviews come first: they are the closest to an offer.
    prep_dirs = [_slug(p.name) for p in (MY_DATA_DIR / "interview-prep").glob("*") if p.is_dir()]
    for r in [r for r in rows if status(r) == "interview"]:
        company = _slug(r.get("Company"))
        if not any(company and company in d for d in prep_dirs):
            actions.append(Action(1, f"Prepare for your interview: {r.get('Job Title')} @ {r.get('Company')}",
                                  "You have an interview. A role brief, story bank and one mock round make the biggest difference.",
                                  say=f"Run interview-coach for {r.get('Job Title')} at {r.get('Company')}."))
        else:
            actions.append(Action(2, f"Do one mock interview round for {r.get('Company')}",
                                  "Short, repeated practice beats one long session the night before.",
                                  say=f"Give me a 15-minute mock interview for {r.get('Company')}, then grade me."))

    apply_now = sorted([r for r in rows if r.get("Verdict") == "apply" and status(r) == "new" and fresh(r)],
                       key=lambda r: -(r.get("Fit %") or 0))
    for r in apply_now[:3]:
        actions.append(Action(3, f"Apply: {r.get('Job Title')} @ {r.get('Company')}",
                              f"Fit {r.get('Fit %')}% and ATS {r.get('ATS %')}%: your CV is ready. "
                              "Then set its Status to Applied in data/jobs.xlsx.",
                              link=str(r.get("Job URL") or "")))

    tailor = sorted([r for r in rows if r.get("Verdict") == "tailor_first" and status(r) == "new" and fresh(r)],
                    key=lambda r: -(r.get("Fit %") or 0))
    for r in tailor[:2]:
        missing = ", ".join([m.strip() for m in str(r.get("Missing ATS Terms") or "").split(",") if m.strip()][:3])
        actions.append(Action(4, f"Tailor your CV, then apply: {r.get('Job Title')} @ {r.get('Company')}",
                              f"Fit {r.get('Fit %')}%, but ATS only {r.get('ATS %')}%: the CV wording would get filtered out"
                              + (f" (missing: {missing})." if missing else "."),
                              say=f"Tailor my CV for {r.get('Job Title')} at {r.get('Company')}: {r.get('Job URL') or '[paste the JD]'}"))

    waiting = []
    for r in rows:
        if status(r) != "applied":
            continue
        applied_on = _first_date(history.get(str(r.get("Job ID") or ""), {}), APPLIED_OR_LATER)
        days = _days_since(applied_on, today)
        if days is not None and days >= FOLLOW_UP_DAYS:
            waiting.append((days, r))
    if waiting:
        waiting.sort(key=lambda x: -x[0])
        names = "; ".join(f"{r.get('Company')} ({d} days)" for d, r in waiting[:3])
        actions.append(Action(5, f"Follow up on {len(waiting)} application(s) with no reply",
                              f"{names}. Send one polite follow-up, or set the Status to 'No reply' so your stats stay accurate.",
                              say=f"Draft a short follow-up email for my application to {waiting[0][1].get('Company')}."))

    # Recurring CV wording the user already has (marked * by the scorer).
    cutoff = (today - timedelta(days=28)).isoformat()
    starred = Counter()
    for r in rows:
        if str(r.get("Date Found", ""))[:10] >= cutoff and (r.get("Fit %") or 0) >= t.alert_min_fit:
            starred.update(m.strip().rstrip("*").lower() for m in str(r.get("Missing ATS Terms") or "").split(",")
                           if m.strip().endswith("*"))
    top = [term for term, n in starred.most_common(2) if n >= 2]
    if top:
        actions.append(Action(6, f"Add to your master CV: {', '.join(top)}",
                              "You have these skills, but your CV doesn't say so, and strong-fit jobs keep asking for them. "
                              "One edit lifts your ATS score on every future job.",
                              say=f"Update my master CV to show {' and '.join(top)}, using only my real experience."))

    applied_recent = sum(1 for r in rows
                         if (_days_since(_first_date(history.get(str(r.get("Job ID") or ""), {}), APPLIED_OR_LATER), today) or 99) <= 7)
    strong_recent = sum(1 for r in rows if fresh(r) and (r.get("Fit %") or 0) >= t.alert_min_fit)
    if rows and applied_recent == 0 and strong_recent == 0:
        actions.append(Action(7, "Widen your search",
                              "No strong matches in the last 10 days. Try 1-2 more job titles or another location.",
                              say="Look at my skill profile and suggest 3 more job titles to search for."))
    return actions


def profile_action(config: Config) -> list[Action]:
    path = ROOT / config.profile_file
    if path.exists() and (time.time() - path.stat().st_mtime) / 86400 > PROFILE_STALE_DAYS:
        return [Action(8, "Refresh your skill profile",
                       f"It's over {PROFILE_STALE_DAYS} days old. New skills and interview lessons make scores fairer.",
                       say="Review my skill profile with me and update anything that changed.")]
    return []


def next_actions(config: Config | None, rows: list[dict], history: dict,
                 today: date | None = None, limit: int = 3) -> list[Action]:
    today = today or date.today()
    setup = setup_actions(config)
    if setup:
        return sorted(setup, key=lambda a: a.priority)[:limit]
    actions = job_actions(rows, history, config, today) + profile_action(config)
    if not actions:
        actions = [Action(9, "Practise one interview question (5 minutes)",
                          "Nothing urgent today. A small daily rep keeps you sharp for when the call comes.",
                          say="Ask me one interview question for my target role and grade my answer.")]
    return sorted(actions, key=lambda a: a.priority)[:limit]


def format_actions(actions: list[Action]) -> str:
    if not actions:
        return ""
    return "\n\n".join(["👉 Your next steps"] + [a.text(i) for i, a in enumerate(actions, 1)])
