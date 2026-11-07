## What this changes

## Security checklist
- [ ] No keys, tokens, CVs or personal data in the diff (including test fixtures and screenshots)
- [ ] New network calls go through `job_alert/http.py`; new output passes through `redact()`
- [ ] The scoring agent still has only Read and Write tools
- [ ] New job sources use an official API or feed (no scraping against a site's terms)
- [ ] Skills still forbid inventing experience and asking for keys in chat
- [ ] `python -m pytest` passes
