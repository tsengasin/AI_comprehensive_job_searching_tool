"""Keep API keys and tokens out of logs, error messages and notifications.

Job-source APIs put the key in the URL (Jooble: /api/<KEY>, SerpApi: ?api_key=,
Telegram: /bot<TOKEN>/). When `requests` raises an error it prints the full URL,
so without this step a single failed request would write your key into a log file.
"""

from __future__ import annotations

import os
import re

# Names of environment variables whose values must never appear in output.
SECRET_ENV_VARS = ("JOOBLE_APP_KEY", "SERPAPI_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID")

_PATTERNS = [
    # ?api_key=XXXX or &api_key=XXXX (SerpApi and many others)
    (re.compile(r"(?i)([?&](?:api_?key|key|token|access_token)=)[^&\s\"']+"), r"\1[REDACTED]"),
    # Telegram: /bot123456:ABC-xyz/
    (re.compile(r"/bot\d+:[A-Za-z0-9_-]+"), "/bot[REDACTED]"),
    # Jooble: jooble.org/api/<key>
    (re.compile(r"(jooble\.org/api/)[^/\s\"']+"), r"\1[REDACTED]"),
    # Authorization headers
    (re.compile(r"(?i)(authorization['\"]?\s*[:=]\s*['\"]?(?:bearer\s+)?)[^\s'\"]+"), r"\1[REDACTED]"),
]


def _secret_values() -> list[str]:
    values = []
    for name in SECRET_ENV_VARS:
        value = os.environ.get(name, "")
        # Very short values (e.g. an empty or 1-2 char placeholder) would cause
        # false positives everywhere, so only redact meaningful lengths.
        if len(value) >= 6:
            values.append(value)
    return values


def redact(text: object) -> str:
    """Return `text` as a string with every known secret removed."""
    out = str(text)
    for value in _secret_values():
        out = out.replace(value, "[REDACTED]")
    for pattern, repl in _PATTERNS:
        out = pattern.sub(repl, out)
    return out


def contains_secret(text: str) -> bool:
    return redact(text) != text
