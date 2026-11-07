# The scoring method: why two numbers

Most AI job matchers give one number, usually a keyword overlap. That number answers the wrong
question, and it is usually too high. This toolkit separates two questions that recruiters and
job seekers mix up.

## 1. ATS Match %: "Will my CV get through?"

Recruiters often say a CV should match **80–85%** of a job ad. They mean **wording**: do the
CV's terms and domain language line up with the JD, so the applicant tracking system (ATS) and a
30-second human scan find what they are looking for?

- Measured against the **CV text only**. If you do something but your CV does not say it, it
  does not count.
- Required terms count double; job-title words 1.5×; nice-to-haves 1×.
- Company-description fluff ("world-class", "elite") is ignored.
- Default bar: **80%** (`ats_target`). Above ~90% usually means keyword stuffing.

## 2. Fit %: "Should I actually apply?"

Your honest overall fit, including your gaps, level and personal background. Default bar:
**85%** (`alert_min_fit`), chosen because in practice jobs above it were the ones that led to
interviews, while lower ones mostly did not.

It applies **hard caps first**, so keyword overlap cannot hide a real mismatch:

| Check | Cap |
|---|---|
| B1 Deal-breaker (language, work permit, location, salary floor) | 50 |
| B2 Required years exceed yours by more than 2 | 70 |
| B3 A *required* skill is one of your known gaps (one / two or more) | 75 / 65 |
| B4 JD wants ownership-level work, your evidence is execution-level | 78 |

Only then does it score how well your proven (Tier 1) and transferable (Tier 2) skills cover
the core of the job, and apply the personal factors in your skill profile.

## The four verdicts

| | ATS ≥ 80 | ATS < 80 |
|---|---|---|
| **Fit ≥ 85** | 🟢 **Apply now** | 🟡 **Tailor CV first**: a good job your CV would lose. The most valuable alert. |
| **Fit 70–84** | 🟠 Stretch: tracked, not alerted | 🟠 Stretch |
| **Fit < 70** | ⚪ Skip (not tracked) | ⚪ Skip |

Full rubric used by the AI: [`.claude/skills/job-match-alert/scoring-rubric.md`](../.claude/skills/job-match-alert/scoring-rubric.md).
Worked example: [`examples/demo-persona/sample-scoring.md`](../examples/demo-persona/sample-scoring.md).

## Limits, honestly

- The ATS score is an **estimate** of keyword alignment. Real ATS products differ, and many
  companies have humans screen first.
- Fit depends on how honest your skill profile is. Garbage in, garbage out.
- A score is a prioritisation aid, not a prediction of getting hired.
