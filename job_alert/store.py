"""Local storage: de-duplication state and the Excel job tracker.

Everything lives in ./data, which is git-ignored. Nothing is uploaded anywhere.
"""

from __future__ import annotations

import json
import time
from datetime import date
from pathlib import Path

from openpyxl import Workbook, load_workbook

from .config import DATA_DIR

STATE_FILE = DATA_DIR / "state.json"
TRACKER_FILE = DATA_DIR / "jobs.xlsx"

TRACKER_COLUMNS = [
    "Date Found", "Verdict", "Fit %", "ATS %", "Job Title", "Company", "Location",
    "Matched Skills", "Missing ATS Terms", "Gap Flags", "Level Fit", "Reason",
    "Salary", "Posted", "Job URL", "Source", "Job ID", "Status",
]


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    (DATA_DIR / "raw").mkdir(exist_ok=True)


# --- de-duplication state -------------------------------------------------

def load_state() -> dict:
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    return {"seen": {}}


def save_state(state: dict) -> None:
    ensure_data_dir()
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


def title_company_key(job: dict) -> str:
    return "tc:" + " ".join(f"{job.get('title', '')}|{job.get('company', '')}".lower().split())


def is_seen(state: dict, job: dict) -> bool:
    seen = state.get("seen", {})
    return job["job_id"] in seen or title_company_key(job) in seen


def mark_seen(state: dict, job: dict) -> None:
    today = date.today().isoformat()
    seen = state.setdefault("seen", {})
    seen[job["job_id"]] = today
    seen[title_company_key(job)] = today


def dedupe(jobs: list[dict], state: dict) -> list[dict]:
    """Drop jobs already processed on earlier days and duplicates across sources."""
    fresh, keys = [], set()
    for job in jobs:
        if not job.get("title") or not job.get("url"):
            continue
        key = title_company_key(job)
        if key in keys or job["job_id"] in keys or is_seen(state, job):
            continue
        keys.update({key, job["job_id"]})
        fresh.append(job)
    return fresh


def prune_raw_files(keep_days: int) -> None:
    cutoff = time.time() - keep_days * 86400
    for path in (DATA_DIR / "raw").glob("*.json"):
        if path.stat().st_mtime < cutoff:
            path.unlink()


# --- tracker --------------------------------------------------------------

def append_to_tracker(rows: list[dict], path: Path = TRACKER_FILE) -> None:
    if not rows:
        return
    ensure_data_dir()
    if path.exists():
        wb = load_workbook(path)
        ws = wb.active
    else:
        wb = Workbook()
        ws = wb.active
        ws.title = "Jobs"
        ws.append(TRACKER_COLUMNS)
    for row in rows:
        ws.append([row.get(col, "") for col in TRACKER_COLUMNS])
    wb.save(path)


def read_tracker(path: Path = TRACKER_FILE) -> list[dict]:
    if not path.exists():
        return []
    ws = load_workbook(path, read_only=True).active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return []
    header = [str(h) for h in rows[0]]
    return [dict(zip(header, r)) for r in rows[1:]]
