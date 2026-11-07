"""A thin wrapper around `requests` that never leaks secrets in its errors."""

from __future__ import annotations

import requests

from .redact import redact

TIMEOUT_SECONDS = 30


class SourceError(RuntimeError):
    """Raised when a job source or notifier fails. The message is already redacted."""


def request_json(method: str, url: str, **kwargs) -> dict:
    kwargs.setdefault("timeout", TIMEOUT_SECONDS)
    try:
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "?"
        # Deliberately do not include the URL or the response body.
        raise SourceError(f"HTTP {status} from {_host(url)}") from None
    except requests.RequestException as exc:
        raise SourceError(f"Network error talking to {_host(url)}: {redact(type(exc).__name__)}") from None
    except ValueError:
        raise SourceError(f"{_host(url)} did not return valid JSON") from None


def _host(url: str) -> str:
    return url.split("/")[2] if "://" in url else "unknown host"
