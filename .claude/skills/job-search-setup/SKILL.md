---
name: job-search-setup
description: Guide a job seeker step by step through setting up this toolkit - folders, CV, skill profile, API keys, Telegram alerts and the daily schedule - without ever handling their keys. Use when the user says "set up", "get started", "install", "how do I start", or runs into a setup error.
---

# Job Search Setup (guided)

You are walking a possibly non-technical person through setup. Go **one step at a time**, confirm
each step worked before moving on, and explain in plain language. Reply in the user's language.

## Hard safety rules

- **Never ask the user to paste an API key, token, password or chat id into the chat.** Tell them
  to open `.env` in a text editor and paste it there themselves. If they paste one anyway, tell
  them to rotate (regenerate) that key, because the chat history now contains it.
- Never print, `cat`, `grep` or otherwise display `.env`. To check keys, run
  `python -m job_alert doctor`, which only says OK/MISSING.
- Never commit `.env`, `config.yaml`, `my-data/` or `data/`. They are git-ignored; keep it that way.
- If the user forked this repo on GitHub, recommend making the fork **private**.

## Steps

1. **Check tools.** Python 3.10+ (`python3 --version`) and Claude Code (`claude --version`).
   If missing, point to docs/01-quick-start.md.
2. **Install packages.** `python3 -m venv .venv`, activate it, `pip install -r requirements.txt`.
3. **CV.** Ask whether they have a CV.
   - Yes: ask them to save it as `my-data/master-cv.md` (or `.docx`). Offer the `cv-builder` skill
     to turn it into a clean master CV.
   - No: start the `cv-builder` skill in "build from scratch" mode.
4. **Skill profile.** Run the `skill-profile-builder` skill. This is what makes the scores honest.
5. **Config.** Copy `config.example.yaml` to `config.yaml`. Help them choose 3–6 search queries
   (real job titles from postings they like) and a location. Explain the two bars:
   `alert_min_fit` (personal fit, default 85) and `ats_target` (CV wording, default 80).
6. **Keys.** Copy `.env.example` to `.env`. Walk them through docs/02-api-keys.md for Jooble,
   SerpApi and Telegram. They paste values into `.env` themselves.
   Then run `python -m job_alert doctor` and `python -m job_alert test-telegram`.
7. **First run.** `python -m job_alert run`. Explain the output and open `data/jobs.xlsx`.
   If almost everything scores 85+, revisit the skill profile: it is probably too generous.
8. **Schedule.** Follow docs/03-scheduling.md for their OS (macOS launchd, Linux cron, Windows
   Task Scheduler).
9. **Wrap up.** Remind them: weekly `python -m job_alert insights`; use `cv-builder` to tailor for
   every `tailor_first` alert; use `interview-coach` once they get an interview.

## Common errors

| Message | Fix |
|---|---|
| `config.yaml not found` | Step 5 |
| `JOOBLE_APP_KEY is not set` | Step 6; check there are no spaces around `=` |
| `HTTP 401/403 from jooble.org` or `serpapi.com` | Key is wrong or not yet activated |
| `HTTP 429` | Free quota used up; reduce queries or wait |
| `Claude Code is logged out` | Run `claude`, then `/login` |
| `Could not find 'claude'` | Set `engine.claude_command` to the full path (`which claude`) |
