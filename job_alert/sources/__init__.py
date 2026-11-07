"""Job sources. Each source returns a list of normalised job dicts:

    {
      "job_id": str,       # stable id used for de-duplication ("<source>:<id>")
      "source": str,
      "title": str,
      "company": str,
      "location": str,
      "url": str,
      "salary": str,
      "posted": str,
      "description": str,
      "query": str,
    }

Only official APIs are used. Do not add scrapers for sites whose terms forbid
automated access (for example LinkedIn).
"""

from __future__ import annotations

from typing import Callable

from . import jooble, serpapi

SOURCES: dict[str, Callable] = {
    "jooble": jooble.fetch,
    "serpapi": serpapi.fetch,
}
