"""Jooble job search API (free key: https://jooble.org/api/about)."""

from __future__ import annotations

from ..config import Config, require_env
from ..http import request_json


def fetch(config: Config, state: dict) -> list[dict]:
    key = require_env("JOOBLE_APP_KEY")
    jobs: list[dict] = []
    for query in config.queries:
        data = request_json(
            "POST",
            f"https://jooble.org/api/{key}",
            json={
                "keywords": query,
                "location": config.location,
                "ResultOnPage": str(config.results_per_query),
            },
        )
        for raw in data.get("jobs", []):
            jobs.append(normalise(raw, query))
    return jobs


def normalise(raw: dict, query: str) -> dict:
    return {
        "job_id": f"jooble:{raw.get('id', '')}",
        "source": "jooble",
        "title": str(raw.get("title", "")).strip(),
        "company": str(raw.get("company", "")).strip(),
        "location": str(raw.get("location", "")).strip(),
        "url": str(raw.get("link", "")).strip(),
        "salary": str(raw.get("salary", "")).strip(),
        "posted": str(raw.get("updated", "")).strip(),
        "description": str(raw.get("snippet", "")).strip(),
        "query": query,
    }
