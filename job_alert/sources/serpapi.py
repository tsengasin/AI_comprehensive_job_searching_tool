"""Google Jobs results through SerpApi (free plan has a monthly quota: https://serpapi.com).

Each query runs at most once per day, so a re-run on the same day does not
burn through the free quota.
"""

from __future__ import annotations

import time
from datetime import date

from ..config import Config, require_env
from ..http import request_json


def fetch(config: Config, state: dict) -> list[dict]:
    key = require_env("SERPAPI_KEY")
    today = date.today().isoformat()
    run_state = state.setdefault("serpapi_runs", {})
    # Forget old days so the state file stays small.
    for day in [d for d in run_state if d != today]:
        del run_state[day]
    already_run = set(run_state.get(today, []))

    jobs: list[dict] = []
    for query in config.queries:
        if query in already_run:
            print(f"[serpapi] '{query}' already ran today, skipping to protect your free quota.")
            continue
        params = {
            "engine": "google_jobs",
            "q": query,
            "location": config.location,
            "hl": config.language,
            "api_key": key,
        }
        data = request_json("GET", "https://serpapi.com/search", params=params)
        for raw in data.get("jobs_results", []):
            jobs.append(normalise(raw, query))
        already_run.add(query)
        run_state[today] = sorted(already_run)
        time.sleep(1)
    return jobs


def normalise(raw: dict, query: str) -> dict:
    apply_options = raw.get("apply_options") or []
    url = apply_options[0].get("link", "") if apply_options else raw.get("share_link", "")
    extensions = raw.get("detected_extensions") or {}
    # SerpApi's job_id is not always stable between runs; fall back to the URL.
    job_id = raw.get("job_id") or url
    return {
        "job_id": f"serpapi:{job_id}",
        "source": "serpapi",
        "title": str(raw.get("title", "")).strip(),
        "company": str(raw.get("company_name", "")).strip(),
        "location": str(raw.get("location", "")).strip(),
        "url": str(url).strip(),
        "salary": str(extensions.get("salary", "")).strip(),
        "posted": str(extensions.get("posted_at", "")).strip(),
        "description": str(raw.get("description", "")).strip(),
        "query": query,
    }
