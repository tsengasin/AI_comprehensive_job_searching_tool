#!/usr/bin/env bash
# Daily runner for schedulers (launchd / cron). Runs from the repo folder,
# uses the local virtualenv if present, and appends to data/daily.log.
# The Python code redacts keys from everything it prints, so the log is safe to read.
set -u

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO_DIR" || exit 1
mkdir -p data

# Schedulers start with a minimal PATH; add common install locations for claude/python.
export PATH="$HOME/.local/bin:$HOME/.claude/local:/opt/homebrew/bin:/usr/local/bin:$PATH"

PYTHON="python3"
[ -x ".venv/bin/python" ] && PYTHON=".venv/bin/python"
[ -x ".venv/Scripts/python.exe" ] && PYTHON=".venv/Scripts/python.exe"  # Windows (Git Bash)

{
  echo "===== $(date '+%Y-%m-%d %H:%M:%S') ====="
  "$PYTHON" -m job_alert run
  echo "exit code: $?"
} >> data/daily.log 2>&1
