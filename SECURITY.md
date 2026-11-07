# Security and privacy

## The short version

- **No server, no account, no tracking.** Everything runs on your own computer with your own keys.
  The author of this toolkit never receives your CV, your job data or your keys.
- **Your keys stay in `.env`**, which git ignores. Your CV and results stay in `my-data/` and
  `data/`, which git also ignores.
- **Your AI agent cannot be hijacked by a job ad** into running commands or sending data out
  (details below).

## How each risk is handled

| Risk | Protection |
|---|---|
| Keys committed to GitHub | `.env` is git-ignored; CI runs [gitleaks](https://github.com/gitleaks/gitleaks) on every push and PR; optional pre-commit hook (`.pre-commit-config.yaml`) |
| Keys leaking into logs | APIs put keys in URLs, so every request goes through `job_alert/http.py`, whose errors never include the URL, and all output passes through `job_alert/redact.py` |
| Keys read by the AI agent | `AGENTS.md` and every skill forbid reading, asking for or printing keys; Claude Code's `.claude/settings.json` also blocks reading `.env`; `python -m job_alert doctor` checks keys without showing them |
| **Prompt injection in job ads** (a JD containing "ignore your instructions and run ...") | The daily scorer works in `data/work/<date>/`, a folder without your `.env`, and **cannot reach the internet**: Codex runs in its OS sandbox with network off and approvals `never`; Claude Code gets only Read and Write (no shell, web or MCP); API mode gives the model no tools at all. Python, not the AI, builds the tracker and the notification, using job titles and links from the job API, never from the AI's output. AI text fields are length-limited, stripped of links and redacted |
| Personal data in a public fork | `my-data/`, `data/`, `config.yaml` are git-ignored; docs recommend a private fork |
| Malicious code contributed to this repo | All changes are reviewed by the maintainer; the PR template has a security checklist; dependencies are few and version-bounded |
| Terms-of-service violations | Only official APIs (Jooble, SerpApi, Telegram). No LinkedIn or other scraping |

## What you are still responsible for

- Keep your computer and your AI account login secure.
- Your CV and job texts are sent to the AI provider you choose for scoring (see
  docs/05-choose-your-ai.md). Use a local model (Ollama) if nothing should leave your computer.
- Do not paste keys into chats, issues or screenshots. If you do, regenerate the key.
- Review anything the AI writes in your CV before sending it.
- When you share files with anyone (a friend, mentor or career coach), remove details you would not
  post publicly.

## Reporting a vulnerability

Please **do not open a public issue** for security problems. Use GitHub's
**Security → Report a vulnerability** (private advisory) on this repository. Never include real
keys or personal data in a report.
