"""Command line entry point.

    python -m job_alert run              # the full daily pipeline
    python -m job_alert fetch            # only fetch + de-duplicate new jobs
    python -m job_alert score            # score the latest fetched jobs and notify
    python -m job_alert insights         # weekly market and CV insights
    python -m job_alert progress         # your progress report (data/progress-report.html)
    python -m job_alert test-telegram    # check your Telegram setup
    python -m job_alert telegram-chat-id # find your Telegram chat id (message your bot first)
    python -m job_alert doctor           # check config, files and keys (never prints keys)
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import date, datetime, timedelta

from . import notify, progress, scoring, store
from .config import DATA_DIR, ROOT, ConfigError, load_config
from .http import SourceError
from .redact import redact
from .sources import SOURCES

INBOX = DATA_DIR / "inbox.json"


def cmd_fetch(config) -> list[dict]:
    store.ensure_data_dir()
    state = store.load_state()
    fetched, errors = [], []
    for name in config.sources:
        source = SOURCES.get(name)
        if source is None:
            errors.append(f"Unknown source '{name}' in config.yaml")
            continue
        try:
            jobs = source(config, state)
            print(f"[{name}] fetched {len(jobs)} jobs")
            fetched.extend(jobs)
        except (SourceError, ConfigError) as exc:
            errors.append(f"[{name}] {exc}")
    store.save_state(state)  # keeps the SerpApi quota guard even if a later step fails

    stamp = date.today().isoformat()
    (DATA_DIR / "raw" / f"jobs-{stamp}.json").write_text(
        json.dumps(fetched, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    store.prune_raw_files(config.keep_raw_days)

    fresh = store.dedupe(fetched, state)[: config.max_jobs_per_run]
    INBOX.write_text(json.dumps(fresh, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"{len(fresh)} new job(s) to score (after removing ones seen before).")
    if errors and not fetched:
        raise SourceError("; ".join(errors))
    for err in errors:
        print(f"Warning: {redact(err)}", file=sys.stderr)
    return fresh


def cmd_score(config) -> None:
    jobs = json.loads(INBOX.read_text(encoding="utf-8")) if INBOX.exists() else []
    t = config.thresholds
    scored: list[dict] = []
    if jobs:
        work = scoring.prepare_workdir(jobs, config)
        print(f"Scoring {len(jobs)} job(s) with your AI agent (sandboxed in {work.relative_to(ROOT)})...")
        scoring.run_agent(work, config)
        scored = scoring.load_scores(work, jobs, t)

    state = store.load_state()
    today = date.today().isoformat()
    rows = []
    for job in scored:
        store.mark_seen(state, job)
        if job["fit"] >= t.tracker_min_fit:
            rows.append({
                "Date Found": today,
                "Verdict": job["verdict"],
                "Fit %": job["fit"],
                "ATS %": job["ats"],
                "Job Title": job["title"],
                "Company": job["company"],
                "Location": job["location"],
                "Matched Skills": ", ".join(job["matched_skills"]),
                "Missing ATS Terms": ", ".join(job["missing_terms"]),
                "Gap Flags": " | ".join(job["gap_flags"]),
                "Level Fit": job["level_fit"],
                "Reason": job["reason"],
                "Salary": job["salary"],
                "Posted": job["posted"],
                "Job URL": job["url"],
                "Source": job["source"],
                "Job ID": job["job_id"],
                "Status": "New",
            })
    store.append_to_tracker(rows)
    store.save_state(state)
    progress.update_history(store.read_tracker())  # note any Status changes you made
    INBOX.write_text("[]", encoding="utf-8")

    alerts = [j for j in scored if j["verdict"] in ("apply", "tailor_first")]
    counts = Counter(j["verdict"] for j in scored)
    print(f"Scored {len(scored)}: {dict(counts)}. Added {len(rows)} to data/jobs.xlsx.")
    notify.send(notify.build_digest(alerts, t.ats_target), config.notify)


def cmd_insights(config, days: int = 7) -> None:
    rows = store.read_tracker()
    since = (datetime.now() - timedelta(days=days)).date().isoformat()
    recent = [r for r in rows if str(r.get("Date Found", "")) >= since]
    if not recent:
        notify.send(f"No tracked jobs in the last {days} days yet.", config.notify)
        return
    t = config.thresholds
    strong = [r for r in recent if (r.get("Fit %") or 0) >= t.alert_min_fit]

    def count(rows_, column, sep=","):
        c = Counter()
        for r in rows_:
            for item in str(r.get(column) or "").split(sep):
                item = item.strip()
                if item:
                    c[item.lower()] += 1
        return c

    lines = [
        f"Weekly insights ({since} to {date.today().isoformat()})",
        f"Tracked: {len(recent)} · Fit >= {t.alert_min_fit}: {len(strong)} · "
        f"of those ATS-ready: {sum(1 for r in strong if (r.get('ATS %') or 0) >= t.ats_target)}",
        "",
        "Words recruiters' ATS looked for that your CV is missing (fix these first if true):",
        *[f"  {term} ({n})" for term, n in count(strong or recent, "Missing ATS Terms").most_common(8)],
        "",
        "Most common reasons you fell short (skill or experience gaps to work on):",
        *[f"  {flag} ({n})" for flag, n in count(recent, "Gap Flags", sep="|").most_common(6)],
        "",
        "Your strengths employers keep asking for:",
        *[f"  {s} ({n})" for s, n in count(recent, "Matched Skills").most_common(8)],
    ]
    text = "\n".join(lines)
    (DATA_DIR / f"insights-{date.today().isoformat()}.md").write_text(text, encoding="utf-8")
    notify.send(text, config.notify)


def cmd_progress(config, send: bool = True) -> None:
    summary, _ = progress.generate(config)
    print(summary)
    print(f"Report saved to {progress.REPORT_FILE.relative_to(ROOT)} (open it in your browser).")
    if send and "telegram" in config.notify and notify.telegram_configured():
        notify.send_telegram(summary)


def progress_day_today(config) -> bool:
    return config.progress_day == date.today().strftime("%A").lower()


def cmd_test_telegram() -> None:
    problems = notify.check_telegram_setup()
    if problems:
        print("Telegram setup problem(s) found in .env:")
        for p in problems:
            print(f"  - {p}")
        sys.exit(1)
    try:
        notify.send_telegram("✅ Your job alert bot is connected.")
    except SourceError as exc:
        print(f"Telegram refused the message: {exc}")
        print(f"What to do: {notify.telegram_hint(str(exc))}")
        sys.exit(1)
    print("Sent a test message. Check Telegram.")


def cmd_telegram_chat_id() -> None:
    try:
        chats = notify.find_chat_ids()
    except SourceError as exc:
        print(f"Could not read your bot's messages: {exc}")
        if "409" in str(exc):
            print("Your bot has a webhook set. Remove it (open the bot's deleteWebhook URL), then retry.")
        else:
            print(f"What to do: {notify.telegram_hint(str(exc))}")
        sys.exit(1)
    if not chats:
        print("No messages found. Open your bot in Telegram, press Start or send 'hi', then run this again.")
        return
    print("Chats that messaged your bot (put the right number in .env as TELEGRAM_CHAT_ID):")
    for chat_id, label in chats:
        print(f"  {chat_id}   {label}")


def cmd_doctor(config) -> None:
    import os
    checks = [
        ("config.yaml", (ROOT / "config.yaml").exists()),
        (f"CV ({config.cv_file})", (ROOT / config.cv_file).exists()),
        (f"Skill profile ({config.profile_file})", (ROOT / config.profile_file).exists()),
    ]
    for name, var in [("jooble", "JOOBLE_APP_KEY"), ("serpapi", "SERPAPI_KEY")]:
        if name in config.sources:
            checks.append((f"{var} in .env", bool(os.environ.get(var))))
    import shutil
    if config.engine.type == "api":
        checks.append(("LLM_API_KEY in .env (engine: api)", bool(os.environ.get("LLM_API_KEY"))))
        checks.append(("engine.model set in config.yaml", bool(config.engine.model)))
    else:
        checks.append((f"'{config.engine.command}' installed (engine: {config.engine.type})",
                       bool(shutil.which(config.engine.command))))
    if "telegram" in config.notify:
        checks.append(("TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env", notify.telegram_configured()))
    for name, ok in checks:
        print(f"{'OK  ' if ok else 'MISSING'}  {name}")
    if not all(ok for _, ok in checks):
        sys.exit(1)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="job_alert", description="Daily AI job-match alert")
    parser.add_argument("command", choices=["run", "fetch", "score", "insights", "progress", "test-telegram",
                                            "telegram-chat-id", "doctor"])
    parser.add_argument("--days", type=int, default=7, help="look-back window for insights")
    args = parser.parse_args(argv)

    if args.command in ("test-telegram", "telegram-chat-id"):
        # Only .env is needed for these, not config.yaml.
        from dotenv import load_dotenv
        load_dotenv(ROOT / ".env")
        try:
            cmd_test_telegram() if args.command == "test-telegram" else cmd_telegram_chat_id()
        except ConfigError as exc:
            print(exc, file=sys.stderr)
            return 1
        return 0

    try:
        config = load_config()
        if args.command == "doctor":
            cmd_doctor(config)
        elif args.command == "fetch":
            cmd_fetch(config)
        elif args.command == "score":
            cmd_score(config)
        elif args.command == "insights":
            cmd_insights(config, args.days)
        elif args.command == "progress":
            cmd_progress(config)
        elif args.command == "run":
            cmd_fetch(config)
            cmd_score(config)
            if progress_day_today(config):
                cmd_progress(config)
        return 0
    except (ConfigError, SourceError, scoring.ScoringError) as exc:
        message = f"Job search FAILED today: {redact(exc)}"
        print(message, file=sys.stderr)
        if args.command in ("run", "score") and notify.telegram_configured():
            try:
                notify.send_telegram(message)
            except SourceError:
                pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
