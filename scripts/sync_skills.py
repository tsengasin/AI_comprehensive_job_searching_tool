"""Copy the skills from .agents/skills (the open standard folder read by Codex,
Gemini CLI, Cursor, GitHub Copilot and others) to .claude/skills (read by Claude Code).

Edit skills only in .agents/skills, then run:  python scripts/sync_skills.py
A test fails if the two folders drift apart.
"""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / ".agents" / "skills"
DST = ROOT / ".claude" / "skills"

if __name__ == "__main__":
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST)
    print(f"Copied {SRC.relative_to(ROOT)} -> {DST.relative_to(ROOT)}")
