import json

import pytest

from job_alert import notify, scoring, store
from job_alert.config import Thresholds
from job_alert.redact import redact
from job_alert.sources import jooble, serpapi


# --- redaction --------------------------------------------------------------

def test_redacts_keys_in_urls(monkeypatch):
    monkeypatch.setenv("SERPAPI_KEY", "supersecretserpkey123")
    assert "supersecret" not in redact("GET https://serpapi.com/search?q=x&api_key=supersecretserpkey123")
    assert redact("https://jooble.org/api/abc-123-def/") == "https://jooble.org/api/[REDACTED]/"
    assert "AAH" not in redact("https://api.telegram.org/bot123456:AAHxyz_secret-token/sendMessage")


def test_redacts_raw_env_values_anywhere(monkeypatch):
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "987654:tokenvalue")
    assert redact("oops 987654:tokenvalue leaked") == "oops [REDACTED] leaked"


# --- normalising and de-duplication -----------------------------------------

def test_normalise_and_dedupe():
    a = jooble.normalise({"id": 1, "title": "CRM Manager", "company": "Acme", "link": "https://x/1"}, "crm")
    b = serpapi.normalise(
        {"job_id": "z", "title": "CRM  manager", "company_name": "ACME", "apply_options": [{"link": "https://y"}]},
        "crm",
    )
    c = jooble.normalise({"id": 2, "title": "Data Analyst", "company": "Beta", "link": "https://x/2"}, "data")
    state = {"seen": {}}
    store.mark_seen(state, c)
    fresh = store.dedupe([a, b, c], state)
    assert [j["job_id"] for j in fresh] == ["jooble:1"]  # b duplicates a, c was seen before


# --- verdicts and validation of the AI output -------------------------------

T = Thresholds(tracker_min_fit=70, alert_min_fit=85, ats_target=80)


@pytest.mark.parametrize("fit,ats,expected", [
    (90, 85, "apply"),
    (88, 60, "tailor_first"),
    (75, 95, "stretch"),
    (50, 99, "skip"),
])
def test_verdict(fit, ats, expected):
    assert scoring.verdict(fit, ats, T) == expected


def test_load_scores_trusts_only_source_data(tmp_path):
    jobs = [{"job_id": "jooble:1", "title": "CRM Manager", "company": "Acme", "url": "https://real/1",
             "location": "", "salary": "", "posted": "", "source": "jooble", "description": ""}]
    (tmp_path / "scored.json").write_text(json.dumps({"results": [
        {"job_id": "jooble:1", "fit_score": 150, "ats_score": "70", "url": "https://evil",
         "reason": "Great fit, see https://evil.example/steal", "matched_skills": ["HubSpot"] * 20},
        {"job_id": "made-up", "fit_score": 99, "ats_score": 99},
    ]}))
    merged = scoring.load_scores(tmp_path, jobs, T)
    assert len(merged) == 1
    job = merged[0]
    assert job["url"] == "https://real/1"
    assert job["fit"] == 100 and job["ats"] == 70 and job["verdict"] == "tailor_first"
    assert "evil" not in job["reason"]
    assert len(job["matched_skills"]) == 8


# --- notifications ----------------------------------------------------------

def test_digest_and_split():
    jobs = [{"title": "T", "company": "C", "fit": 88, "ats": 60, "verdict": "tailor_first",
             "missing_terms": ["Braze"], "url": "https://u"}]
    text = notify.build_digest(jobs, 80)
    assert "tailor CV first" in text and "Braze" in text
    assert notify.build_digest([], 80).startswith("Daily job search: no new")
    parts = notify.split_message("a" * 9000)
    assert all(len(p) <= notify.TELEGRAM_LIMIT for p in parts) and "".join(parts) == "a" * 9000


def test_tracker_roundtrip(tmp_path):
    path = tmp_path / "jobs.xlsx"
    store.append_to_tracker([{"Job Title": "A", "Fit %": 90}], path)
    store.append_to_tracker([{"Job Title": "B", "Fit %": 72}], path)
    rows = store.read_tracker(path)
    assert [r["Job Title"] for r in rows] == ["A", "B"]


# --- AI engines -------------------------------------------------------------

from pathlib import Path

from job_alert.config import Config, EngineConfig, ROOT


def _config(**engine):
    return Config(queries=["q"], location="x", engine=EngineConfig(**engine))


def test_codex_command_is_sandboxed(tmp_path):
    cmd = scoring.codex_command(_config(type="codex", command="codex"), tmp_path)
    joined = " ".join(cmd)
    assert cmd[:2] == ["codex", "exec"]
    assert "--sandbox workspace-write" in joined
    assert "sandbox_workspace_write.network_access=false" in joined
    assert 'approval_policy="never"' in joined
    assert "dangerously" not in joined and "danger-full-access" not in joined


def test_claude_command_has_no_shell():
    cmd = scoring.claude_command(_config(type="claude", command="claude"))
    assert cmd[cmd.index("--tools") + 1] == "Read,Write"
    assert "bypassPermissions" not in cmd and "--strict-mcp-config" in cmd


# Obviously fake, low-entropy value so secret scanners do not flag the test.
FAKE_KEY = "fake-key-for-tests"


def test_api_engine_batches_and_writes_scores(tmp_path, monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", FAKE_KEY)
    for name in ("scoring-rubric.md", "cv.md", "skill-profile.md"):
        (tmp_path / name).write_text("x")
    jobs = [{"job_id": f"j{i}"} for i in range(5)]
    (tmp_path / "jobs.json").write_text(json.dumps(jobs))
    calls = []

    def fake_request(method, url, **kwargs):
        calls.append((url, kwargs["headers"]))
        batch = json.loads(kwargs["json"]["messages"][1]["content"].split("```json\n")[1].split("\n```")[0])
        body = json.dumps({"results": [{"job_id": j["job_id"], "fit_score": 90, "ats_score": 80} for j in batch]})
        return {"choices": [{"message": {"content": "```json\n" + body + "\n```"}}]}

    monkeypatch.setattr("job_alert.http.request_json", fake_request)
    cfg = _config(type="api", base_url="https://api.example.com/v1", model="m", batch_size=2, key_header="api-key")
    scoring.run_api(tmp_path, cfg)
    assert len(calls) == 3 and calls[0][0] == "https://api.example.com/v1/chat/completions"
    assert calls[0][1] == {"api-key": FAKE_KEY}
    assert len(json.loads((tmp_path / "scored.json").read_text())["results"]) == 5


def test_redacts_openai_style_keys():
    fake = "sk-" + "a" * 24  # built at runtime: matches the pattern, but is not a key
    assert fake not in redact(f"error with {fake}")


def test_claude_skills_copy_matches_agents_skills():
    src, dst = ROOT / ".agents" / "skills", ROOT / ".claude" / "skills"
    files = lambda d: {p.relative_to(d): p.read_bytes() for p in d.rglob("*") if p.is_file()}
    assert files(src) == files(dst), "Run: python scripts/sync_skills.py"


# --- progress report --------------------------------------------------------

from datetime import date as _date

from job_alert import progress


def test_progress_loop(tmp_path, monkeypatch):
    monkeypatch.setattr(progress, "HISTORY_FILE", tmp_path / "h.json")
    monkeypatch.setattr(progress, "MY_DATA_DIR", tmp_path)
    monkeypatch.setattr(store, "DATA_DIR", tmp_path)
    cfg = Config(queries=["q"], location="x")
    rows = [{"Job ID": f"j{i}", "Date Found": "2026-10-20", "Fit %": 88, "ATS %": 70 + i,
             "Status": "New", "Missing ATS Terms": "braze, sql*", "Gap Flags": "B3: Braze"} for i in range(6)]
    progress.update_history(rows, _date(2026, 10, 20))
    for r in rows:
        r["Status"] = "Applied"
    rows[0]["Status"] = "Interview"
    history = progress.update_history(rows, _date(2026, 10, 27))
    assert history["j0"] == {"new": "2026-10-20", "interview": "2026-10-27"}
    assert history["j1"]["applied"] == "2026-10-27"

    weeks = progress.build_weeks(rows, history, cfg, today=_date(2026, 11, 7))
    s = progress.summarise(weeks, rows, history, cfg)
    assert s["applied_recent"] == 6 and s["interviews_recent"] == 1
    assert round(s["rate_recent"]) == 17 and s["focus_terms"][0] == ("braze", 6)
    html_out = progress.render_html(weeks, s, cfg)
    assert "17%" in html_out and "<svg" in html_out
    assert "Interview rate: 17%" in progress.text_summary(s, cfg)


def test_nice_axis_max():
    assert progress._nice_max(3.6) == 4 and progress._nice_max(7) == 10 and progress._nice_max(45) == 100
