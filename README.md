# AI Comprehensive Job Searching Tool

**Free AI skills for job seekers: build and tailor your CV, prepare for interviews, and get a
daily alert only for jobs you genuinely fit. Works with ChatGPT / Codex, Claude, or any
OpenAI-compatible model. Runs on your own computer. No server, no sign-up, no data collection.**

[繁體中文說明](README.zh-Hant.md)

<p align="center"><img src="docs/images/how-it-works.png" alt="How to use it in 6 steps: 1 Download, 2 Set up in Codex or Claude Code, 3 Build an honest skill profile, 4 Daily alerts (Fit 85% + ATS 80%) to Telegram, 5 Tailor CV for strong-fit jobs, 6 Interview prep. Steps 4 to 6 repeat with weekly insights." width="560"></p>

---

## What it does

| | Skill | You say... | You get |
|---|---|---|---|
| 1 | **cv-builder** | "Build my CV" / "Tailor my CV for this job" | A master CV, tailored versions with an ATS keyword check, a change log and a gap analysis. Never invents experience. |
| 2 | **interview-coach** | "I have an interview at X on Friday" | Role brief, STAR story bank, question bank, graded mock interviews, tough-conversation drills, a day-by-day plan to close skill gaps, and a practice log |
| 3 | **job-match-alert** | "Should I apply to this?" (or runs daily) | Two scores per job, **Fit %** and **ATS Match %**, a Telegram digest of jobs that clear your bar, a spreadsheet tracker, and weekly insights |
| + | **skill-profile-builder** | "What are my real strengths and gaps?" | An honest Tier 1/2/3 skill profile, level check and personal factors. This is what makes the scores trustworthy |
| + | **job-search-setup** | "Help me set up" | A step-by-step guided setup |

## A job search that improves itself

Most job searches feel like sending applications into a void. This toolkit runs a loop:
**find → act → record → measure → improve**. Every job you see, every application and every
reply feeds the next week: the CV terms you are missing, the skills that keep capping your fit,
and whether your changes worked.

Every week you get a **progress report**: interview rate, applications, how well your CV wording
now matches job language, the effort you put in, and one clear focus for next week. So even in a
slow week you can see what is improving and what to work on. → [How the loop works](docs/07-progress-loop.md)

<p align="center"><img src="docs/images/progress-report-example.png" alt="Example weekly progress report with sample data: interview rate, applications per week, CV wording trend and next week's focus" width="720"></p>

## Why two scores?

Recruiters say your CV should match **80–85%** of a job ad. That is about **wording**: will
the ATS and a 30-second scan find the right terms? Whether you should apply is a different
question: **honest fit**, including your gaps, level, language, visa and background.

This toolkit scores both, and applies hard caps so keyword overlap can't hide a real mismatch
(e.g. a required skill you don't have, or a "head of" role when your evidence is executor-level).

| | ATS ≥ 80 | ATS < 80 |
|---|---|---|
| **Fit ≥ 85** | 🟢 Apply now | 🟡 **Tailor CV first**: a job you fit that your CV would lose |
| **Fit < 85** | 🟠 Stretch / ⚪ Skip | 🟠 Stretch / ⚪ Skip |

The 85% fit bar comes from real use: in the author's own search, jobs above it were the ones
that led to interviews. → [Full method](docs/04-scoring-method.md) ·
[Worked example](examples/demo-persona/sample-scoring.md)

## Get started

Pick the path that matches the AI you already use:

| You use... | Do this | What you get |
|---|---|---|
| **ChatGPT in the browser only** | Upload the skill files to a ChatGPT Project ([10-minute guide](docs/06-use-in-chatgpt.md)) | CV, skill profile, interview prep, score any job you paste |
| **Codex** (ChatGPT plan) or **Claude Code** | Download this repo, open the folder, type **"Help me set up the job search tool."** | Everything, including the daily alert |
| **An API key** (OpenAI, Azure OpenAI, DeepSeek, Qwen, OpenRouter) or **Ollama** | Same as above with any agent, and `engine.type: api` | Everything, including the daily alert |

Download: **Code → Download ZIP** (or fork it and **make your fork private**).
Step by step: [Quick start](docs/01-quick-start.md) · Which AI? [Choose your AI](docs/05-choose-your-ai.md)

The CV and interview skills need no keys. The daily alert also needs free keys from Jooble
and/or SerpApi and a Telegram bot ([how](docs/02-api-keys.md)).

## Your data and keys are safe by design

- Runs **100% on your computer**. The author never receives your CV, data or keys.
- Keys live in `.env`; CV and results in `my-data/` and `data/`. All git-ignored.
- The daily AI scorer runs sandboxed with **no internet access**, so a malicious job ad can't
  trick it into leaking anything.
- Official APIs only. No LinkedIn scraping.

→ [SECURITY.md](SECURITY.md)

## How the daily alert works

```
 Jooble / SerpApi ──► fetch & de-duplicate ──► AI scores (Codex / Claude / API, sandboxed)
                                                      │
 Telegram digest ◄── tracker data/jobs.xlsx ◄── Python validates scores & sets verdicts
```

```bash
python -m job_alert run        # daily pipeline
python -m job_alert insights   # weekly: missing CV terms, recurring gaps, strengths in demand
python -m job_alert progress   # your progress report: interview rate, CV wording, effort, focus
python -m job_alert doctor     # check setup without showing keys
```

## Repo map

| Path | What |
|---|---|
| `.agents/skills/` | The five skills (plain Markdown, [Agent Skills](https://agentskills.io) format); `.claude/skills/` is a copy for Claude Code |
| `job_alert/` | Daily alert pipeline (Python) |
| `docs/` | Quick start, keys, scheduling, scoring method |
| `templates/` | Skill profile, CV and mock-interview log templates |
| `examples/demo-persona/` | A fictional job seeker's CV, profile and sample scoring |
| `my-data/` | **Your** private files (git-ignored) |

## Contributing

Issues and PRs welcome, especially new official job sources, translations, and interview
modules. Please read [SECURITY.md](SECURITY.md) first, and never include real keys or personal
data in an issue.

## License

[MIT](LICENSE). See also the [disclaimer](DISCLAIMER.md): scores are estimates, not guarantees.
