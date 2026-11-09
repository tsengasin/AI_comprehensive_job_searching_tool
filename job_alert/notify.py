"""Notifications. Messages go only to YOUR chat; the bot token never leaves .env."""

from __future__ import annotations

import os
import re

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


# Telegram's error text -> what to do about it.
TELEGRAM_HINTS = [
    ("bots can't send messages to bots",
     "TELEGRAM_CHAT_ID is your bot's own id (the number before ':' in the token). "
     "Use YOUR chat id instead: message @userinfobot in Telegram, or run "
     "`python -m job_alert telegram-chat-id` (docs/02-api-keys.md, Step 3)."),
    ("can't initiate conversation",
     "Telegram only lets a bot message you after you message it first. Open your bot in "
     "Telegram, press Start (or send 'hi'), then try again."),
    ("blocked by the user",
     "You blocked the bot. In Telegram open the bot, tap Restart/Unblock, send 'hi', then try again."),
    ("not a member", "The bot is not in that group or channel. Add the bot to it first."),
    ("kicked", "The bot was removed from that group. Add it back, then try again."),
    ("chat not found",
     "Telegram doesn't know that chat id. Send your bot a message, then get your id from "
     "@userinfobot or `python -m job_alert telegram-chat-id` (docs/02-api-keys.md, Step 3)."),
    ("unauthorized", "TELEGRAM_BOT_TOKEN is wrong or was revoked. Copy it again from @BotFather."),
    ("not found", "TELEGRAM_BOT_TOKEN looks malformed. It should look like 123456789:AAE...xyz"),
]

_CHAT_ID_FORMAT = re.compile(r"^(-?\d+|@[A-Za-z0-9_]{5,})$")


def telegram_hint(error: str) -> str:
    low = error.lower()
    for needle, hint in TELEGRAM_HINTS:
        if needle in low:
            return hint
    if "api.telegram.org:" not in low:
        # No explanation from Telegram itself: something between you and Telegram refused it.
        return ("The refusal did not come from Telegram. A work/school network, firewall, proxy or VPN "
                "may be blocking api.telegram.org. Try another network or turn the VPN off/on.")
    return "Check TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env (see docs/02-api-keys.md)."


def check_telegram_setup() -> list[str]:
    """Problems we can spot without calling Telegram. Never returns the values themselves."""
    problems = []
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        return ["TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must both be set in .env."]
    if chat_id != chat_id.strip("'\""):
        problems.append("Remove the quotes around TELEGRAM_CHAT_ID in .env.")
    elif not _CHAT_ID_FORMAT.match(chat_id):
        problems.append("TELEGRAM_CHAT_ID should be only digits (groups start with '-'), "
                        "with no spaces or other text.")
    if ":" in token and chat_id.lstrip("-") == token.split(":", 1)[0]:
        problems.append(TELEGRAM_HINTS[0][1])
    if ":" not in token:
        problems.append(TELEGRAM_HINTS[-1][1])
    return problems


def find_chat_ids() -> list[tuple[str, str]]:
    """Chats that have messaged the bot recently: [(chat_id, label)]."""
    token = require_env("TELEGRAM_BOT_TOKEN")
    data = request_json("GET", f"https://api.telegram.org/bot{token}/getUpdates")
    chats = {}
    for update in data.get("result", []):
        message = update.get("message") or update.get("channel_post") or update.get("my_chat_member") or {}
        chat = message.get("chat") or {}
        if "id" in chat:
            label = chat.get("title") or " ".join(filter(None, [chat.get("first_name"), chat.get("last_name")]))
            chats[str(chat["id"])] = f"{label or 'unknown'} ({chat.get('type', '?')})"
    return list(chats.items())


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
