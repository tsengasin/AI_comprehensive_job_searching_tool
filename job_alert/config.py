"""Load config.yaml (your search settings) and .env (your keys)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
MY_DATA_DIR = ROOT / "my-data"


class ConfigError(RuntimeError):
    pass


@dataclass
class Thresholds:
    tracker_min_fit: int = 70   # keep in the tracker so you can review it
    alert_min_fit: int = 85     # your personal "worth applying" bar
    ats_target: int = 80        # recruiter / ATS wording bar for the CV


@dataclass
class EngineConfig:
    """Which AI scores the jobs. See docs/05-choose-your-ai.md."""
    type: str = "codex"                 # codex | claude | api
    command: str = ""                   # path to the codex / claude CLI (default: on PATH)
    base_url: str = "https://api.openai.com/v1"  # api only: any OpenAI-compatible endpoint
    model: str = ""                     # api only, e.g. gpt-4.1-mini, deepseek-chat, qwen-plus
    batch_size: int = 10                # api only: jobs per request
    key_header: str = "Authorization"   # api only: "api-key" for Azure OpenAI


@dataclass
class Config:
    queries: list[str]
    location: str
    country: str = ""
    sources: list[str] = field(default_factory=lambda: ["jooble", "serpapi"])
    language: str = "en"
    results_per_query: int = 40
    max_jobs_per_run: int = 60
    max_description_chars: int = 6000
    keep_raw_days: int = 3
    thresholds: Thresholds = field(default_factory=Thresholds)
    notify: list[str] = field(default_factory=lambda: ["telegram"])
    cv_file: str = "my-data/master-cv.md"
    profile_file: str = "my-data/skill-profile.md"
    engine: EngineConfig = field(default_factory=EngineConfig)


def load_config(path: Path | None = None) -> Config:
    load_dotenv(ROOT / ".env")
    path = path or ROOT / "config.yaml"
    if not path.exists():
        raise ConfigError(
            "config.yaml not found. Copy config.example.yaml to config.yaml and edit it "
            "(see docs/01-quick-start.md)."
        )
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    search = raw.get("search", {})
    scoring = raw.get("scoring", {})
    if not search.get("queries") or not search.get("location"):
        raise ConfigError("config.yaml needs search.queries (a list) and search.location.")

    thresholds = Thresholds(
        tracker_min_fit=int(scoring.get("tracker_min_fit", 70)),
        alert_min_fit=int(scoring.get("alert_min_fit", 85)),
        ats_target=int(scoring.get("ats_target", 80)),
    )
    profile = raw.get("profile", {})
    return Config(
        queries=[str(q) for q in search["queries"]],
        location=str(search["location"]),
        country=str(search.get("country", "")),
        sources=list(search.get("sources", ["jooble", "serpapi"])),
        language=str(search.get("language", "en")),
        results_per_query=int(search.get("results_per_query", 40)),
        max_jobs_per_run=int(scoring.get("max_jobs_per_run", 60)),
        max_description_chars=int(scoring.get("max_description_chars", 6000)),
        keep_raw_days=int(raw.get("storage", {}).get("keep_raw_days", 3)),
        thresholds=thresholds,
        notify=list(raw.get("notify", {}).get("channels", ["telegram"])),
        cv_file=str(profile.get("cv_file", "my-data/master-cv.md")),
        profile_file=str(profile.get("skill_profile_file", "my-data/skill-profile.md")),
        engine=_engine(raw.get("engine", {})),
    )


def _engine(raw: dict) -> EngineConfig:
    engine_type = str(raw.get("type", "codex")).lower()
    if engine_type not in ("codex", "claude", "api"):
        raise ConfigError("engine.type in config.yaml must be codex, claude or api.")
    # Older configs used engine.claude_command
    command = raw.get("command") or raw.get("claude_command") or ""
    return EngineConfig(
        type=engine_type,
        command=str(command or ("claude" if engine_type == "claude" else "codex")),
        base_url=str(raw.get("base_url", "https://api.openai.com/v1")).rstrip("/"),
        model=str(raw.get("model", "")),
        batch_size=max(1, int(raw.get("batch_size", 10))),
        key_header=str(raw.get("key_header", "Authorization")),
    )


def require_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ConfigError(f"{name} is not set. Add it to your .env file (never to config.yaml or chat).")
    return value
