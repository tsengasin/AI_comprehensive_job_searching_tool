# Demo persona: test the toolkit without using your own data

Everything in this folder is **fictional**. Alex Chan is not a real person and the companies do
not exist. Use these files to try every skill before you add your own CV.

| File | What it is |
|---|---|
| `master-cv.md` / `master-cv.docx` | Alex's CV (5 years in CRM and lifecycle marketing, Hong Kong) |
| `skill-profile.md` | Alex's finished skill profile (what `skill-profile-builder` produces) |
| `sample-jd-crm-manager.md` | A job Alex fits but whose CV wording falls short → expect 🟡 tailor first |
| `sample-jd-senior-lifecycle-b2b.md` | A job with lots of shared keywords but a real level and tool gap → expect 🟠 stretch |
| `sample-scoring.md` | Worked example of the two scores |

## 10-minute test drive

1. Copy the demo files into your private folder:

```bash
cp examples/demo-persona/master-cv.md examples/demo-persona/skill-profile.md my-data/
```

(Windows: copy the two files into `my-data` with File Explorer. ChatGPT Project users: upload
them to the project instead.)

2. Ask your AI, one at a time:

| Try | Say | What good looks like |
|---|---|---|
| Score a job | "Should I apply? Here's the JD: [paste sample-jd-crm-manager.md]" | Fit ≈ 85–90, ATS ≈ 65–72, verdict 🟡, missing terms like *customer retention strategy*\*, *RFM analysis*\*, *Klaviyo* |
| Check it doesn't inflate | Same with `sample-jd-senior-lifecycle-b2b.md` | Caps B2/B3/B4 triggered (7+ years, Braze/Salesforce required, team lead); Fit well below 85 |
| Tailor the CV | "Tailor my CV for the CRM Manager job" | ATS rises to about 80–85, a change log, **no invented tools** (Klaviyo must not appear as a skill) |
| Interview prep | "Run interview-coach for Lumière Beauty, CRM Manager, interview on Friday" | Role brief, STAR stories from Alex's real bullets, then mock questions one at a time |
| Skill profile | Delete `my-data/skill-profile.md`, then "Run skill-profile-builder" | Up to 8 questions, then a Tier 1/2/3 profile close to the demo one |

Scores vary a little between AI models and runs; within ±5 points is normal.

3. When you are done, delete the demo files from `my-data/` and add your own CV.

The `.docx` version is there to check that Word CVs work (`profile.cv_file: my-data/master-cv.docx`
in `config.yaml`).
