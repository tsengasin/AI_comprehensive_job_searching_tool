---
name: skill-profile-builder
description: Build an honest skill profile (Tier 1 strong / Tier 2 transferable / Tier 3 known gaps, level evidence, personal factors and deal-breakers) from the user's CV through a short interview. Use before job matching, when the user asks "what are my strengths/gaps", or when job scores look inflated.
---

# Skill Profile Builder

The skill profile is the backbone of honest job matching. A CV shows what someone *claims*; the
profile records what they can *defend in an interview*, what they genuinely lack, and the
personal factors that change which jobs fit. Reply in the user's language.

Output: `my-data/skill-profile.md`, using `templates/skill-profile.template.md`.
See `examples/demo-persona/skill-profile.md` for a finished example.

## Process

1. **Read the CV** (`my-data/master-cv.md` or `.docx`). If there is none, suggest `cv-builder` first.
2. **Draft tiers from evidence, not job titles.** For each skill or tool in the CV, place it:
   - **Tier 1, Strong / hands-on:** used repeatedly, can explain trade-offs, has a result or example.
   - **Tier 2, Working knowledge / transferable:** used occasionally, or a close equivalent
     (e.g. HubSpot admin → Salesforce concepts). Write the transfer argument next to it.
   - **Tier 3, Known gaps:** common in target JDs but not genuinely held.
3. **Interview the user, max 8 questions, one at a time.** Focus on:
   - Skills where the CV is vague ("exposure to", "familiar with"): how deep, really?
   - Tools that appear in target job ads they have not mentioned: ever used them?
   - Level: did they *own* outcomes (budget, roadmap, team) or *execute* within someone else's plan?
     Ask for one concrete example.
   - Years of relevant experience per target function (not total career years).
   - Personal factors: languages (and level), work authorisation / visa needs, location and remote
     constraints, salary floor, industries to avoid or prefer, career-change context, caring or
     scheduling constraints they want respected. Only record what they choose to share.
4. **Push back on overclaiming, kindly.** If something lands in Tier 1 without an example, ask for
   one or move it to Tier 2. It is better to discover a gap here than in an interview.
5. **Level Check section:** list the verbs their evidence supports (Executor: supported,
   executed, coordinated; Operator: led, built, defined, managed; Senior: owned, set strategy,
   managed managers) and which ones to avoid claiming.
6. **Domain keyword bank:** for each target function, list the phrases JDs use for things they
   genuinely do (this feeds ATS wording in `cv-builder`).
7. Save the file. Summarise in 5 bullets: top strengths, top 3 gaps that block the most jobs,
   and one suggestion for closing the most valuable gap.

## Rules

- Never add a skill the user did not confirm.
- Keep sensitive personal factors minimal and phrased neutrally (e.g. "Needs visa sponsorship
  outside Hong Kong"). The file is private, but it may later be shared with a mentor or career coach.
- Update the profile whenever the user learns something new or a job score feels wrong.
