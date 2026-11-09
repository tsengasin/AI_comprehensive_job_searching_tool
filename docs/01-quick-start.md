# Quick start (about 45 minutes, no coding needed)

You need: a computer (macOS, Windows or Linux) and one AI tool:
**Codex** (with a ChatGPT plan), **Claude Code** (with a Claude plan), or an **API key** from any
OpenAI-compatible provider. Not sure which? See [05-choose-your-ai.md](05-choose-your-ai.md).
Only use ChatGPT in the browser? See [06-use-in-chatgpt.md](06-use-in-chatgpt.md) instead.

> **Easiest path:** do Step 1, open the folder in Codex or Claude Code, and type
> **"Help me set up the job search tool."** The `job-search-setup` skill walks you through the rest.
> "Your AI" below means whichever of these you use.

## Step 1: Get the toolkit

**Option A, download (simplest):** on GitHub click **Code → Download ZIP**, unzip it somewhere
like `Documents/job-search`.

**Option B, fork:** if you fork it on GitHub, set your fork to **Private**
(Settings → General → Danger Zone → Change visibility). Your CV and job data are git-ignored, but
a private fork is a second safety net.

## Step 2: Install Python packages

Open a terminal in the folder (macOS: right-click the folder → *New Terminal at Folder*;
Windows: open the folder, type `cmd` in the address bar).

```bash
python3 -m venv .venv
```

```bash
source .venv/bin/activate
```
(Windows: `.venv\Scripts\activate`)

```bash
pip install -r requirements.txt
```

## Step 3: Your CV

> **Want to test first?** Use the fictional demo CV and job ads in
> [`examples/demo-persona/`](../examples/demo-persona/README.md) (10-minute test drive).

Put your CV in `my-data/` as `master-cv.md` (or `master-cv.docx`). No CV yet? Ask your AI
in the folder: *"Use cv-builder to build my master CV from scratch."*

## Step 4: Your skill profile (the important part)

Ask your AI: *"Run skill-profile-builder."* It asks up to 8 questions and writes
`my-data/skill-profile.md`: your real strengths, transferable skills, honest gaps, and personal
factors (languages, visa, location). This is what stops the scores from being inflated.

## Step 5: Search settings

Copy `config.example.yaml` to `config.yaml` and edit the job titles and location. Set
`engine.type` to `codex`, `claude` or `api` ([05-choose-your-ai.md](05-choose-your-ai.md)).
Leave the default bars unless you have a reason: **Fit 85** (honest fit) and **ATS 80**
(CV wording). See [04-scoring-method.md](04-scoring-method.md).

## Step 6: Keys (stay on your computer)

Copy `.env.example` to `.env`, then follow [02-api-keys.md](02-api-keys.md).
**Paste keys into `.env` yourself. Never paste them into an AI chat.**

Check everything (prints only OK / MISSING, never your keys):

```bash
python -m job_alert doctor
```

```bash
python -m job_alert test-telegram
```

## Step 7: First run

```bash
python -m job_alert run
```

You get a Telegram digest and a spreadsheet at `data/jobs.xlsx`.

## Step 8: Run it every morning

See [03-scheduling.md](03-scheduling.md).

## What next

| Situation | Say to your AI |
|---|---|
| 🟡 "Tailor CV first" alert | "Tailor my CV for this job: [paste JD]" |
| Got an interview | "Run interview-coach for [company, role, date]" |
| End of the week | "Show my weekly insights" (or `python -m job_alert insights`) |
| Scores feel wrong | "Review my skill profile; my scores feel too high" |
| After applying / hearing back | Update **Status** in `data/jobs.xlsx` ([why](07-progress-loop.md)) |
| Feeling stuck | "How am I progressing?" (or `python -m job_alert progress`) |
