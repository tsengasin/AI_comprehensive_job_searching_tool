"""Notifications. Messages go only to YOUR chat; the bot token never leaves .env."""

from __future__ import annotations

import os

from .config import require_env
from .http import request_json
from .redact import redact

TELEGRAM_LIMIT = 4000  # Telegram's hard limit is 4096 characters per message

VERDICT_LABELS = {
    "apply": "🟢 Apply now",
    "tailor_first": "🟡 Strong fit, tailor CV first",
}


def build_digest(jobs: list[dict], ats_target: int) -> str:
    if not jobs:
        return "Daily job search: no new jobs cleared your bar today."
    lines = [f"Daily job digest: {len(jobs)} job(s) cleared your bar", ""]
    for job in sorted(jobs, key=lambda j: (-j["fit"], -j["ats"])):
        lines.append(f"{VERDICT_LABELS.get(job['verdict'], job['verdict'])}")
        lines.append(f"{job['title']} @ {job['company']}")
        lines.append(f"Fit {job['fit']}% · ATS {job['ats']}% (target {ats_target}%)")
        if job["verdict"] == "tailor_first" and job.get("missing_terms"):
            lines.append("Add to CV if true: " + ", ".join(job["missing_terms"][:5]))
        lines.append(job["url"])
        lines.append("")
    return "\n".join(lines).strip()


def split_message(text: str, limit: int = TELEGRAM_LIMIT) -> list[str]:
    parts, current = [], ""
    for block in text.split("\n\n"):
        candidate = f"{current}\n\n{block}" if current else block
        if len(candidate) <= limit:
            current = candidate
            continue
        if current:
            parts.append(current)
        while len(block) > limit:
            parts.append(block[:limit])
            block = block[limit:]
        current = block
    if current:
        parts.append(current)
    return parts


def send_telegram(text: str) -> None:
    token = require_env("TELEGRAM_BOT_TOKEN")
    chat_id = require_env("TELEGRAM_CHAT_ID")
    for part in split_message(redact(text)):
        request_json(
            "POST",
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": part, "disable_web_page_preview": True},
        )


def send(text: str, channels: list[str]) -> None:
    """Send to every configured channel. Unknown channels are printed to the terminal."""
    for channel in channels:
        if channel == "telegram":
            send_telegram(text)
        elif channel == "terminal":
            print(text)
        else:
            print(f"[notify] Unknown channel '{channel}', printing instead:\n{text}")


def telegram_configured() -> bool:
    return bool(os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"))
