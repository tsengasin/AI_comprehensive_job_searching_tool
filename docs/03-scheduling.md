# Run it automatically every morning

The computer must be on (or asleep, on macOS) at the scheduled time. The job runs
`scripts/run_daily.sh`, which writes to `data/daily.log`. If a run fails (for example your AI
tool is logged out), you get a Telegram message saying why.

## macOS (launchd)

1. In the repo folder run `pwd` and copy the path.
2. Open `scripts/schedule/com.jobsearch.daily.plist` and replace `REPLACE_WITH_REPO_PATH` with it.
   Change `Hour`/`Minute` if you like.
3. Install and load it:

```bash
cp scripts/schedule/com.jobsearch.daily.plist ~/Library/LaunchAgents/
```

```bash
launchctl load ~/Library/LaunchAgents/com.jobsearch.daily.plist
```

4. Test it now instead of waiting for tomorrow:

```bash
launchctl start com.jobsearch.daily
```

If the log says `Could not find 'codex'` (or `claude`), run `which codex` and put that full
path in `config.yaml` → `engine.command`.

## Linux (cron)

```bash
crontab -e
```

Add this line (8:00 every day; replace the path):

```
0 8 * * * /bin/bash /home/you/job-search/scripts/run_daily.sh
```

## Windows (Task Scheduler)

1. Install [Git for Windows](https://git-scm.com/download/win) (it includes Bash), or use WSL.
2. Task Scheduler → *Create Basic Task* → Daily, 8:00.
3. Action: *Start a program*
   - Program: `C:\Program Files\Git\bin\bash.exe`
   - Arguments: `scripts/run_daily.sh`
   - Start in: the repo folder, e.g. `C:\Users\you\Documents\job-search`

## Don't want a schedule?

Just run `python -m job_alert run` when you want, or paste a JD into your AI and ask
"Should I apply?" (the `job-match-alert` skill scores it on the spot).
