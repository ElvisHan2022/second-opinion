# AGENTS.md: Credence (working name), evidence-graded wellness coach

Instructions for any agent working in this repo: Claude Code, a Kordi local or cloud agent, or a teammate's agent. Kordi imports this file into memory, so each bullet is written to stand alone in under 500 characters.

## Project

- Credence is a voice wellness coach for GLP-1 and peptide users. It turns a spoken intake into a persona, answers questions with options graded by evidence, and shows where medical evidence and public opinion agree or split.
- The research theme is trust: measure the gap between how much a user trusts advice and how much the evidence warrants, and the threshold at which a user is willing to act.
- Built at the AI in Science Collaboration Hackathon, Stanford, Nov 16 2026. Judged on novelty, use of Kordi traces for collaboration, and bugs caught.

## Read before building

- `SPEC.md` is the build spec and the source of truth for scope, file layout and acceptance checks.
- `docs/03_evidence_grading_rubric.md` holds the source tiers and grading rules R1 to R6.
- `docs/06_trust_evaluation_loop.md` holds the persona twin and evidence auditor prompts and the stakeholder feedback rules.
- `docs/KORDI_WORKFLOW.md` explains how the team uses Kordi groups, documents, ratings and trace export.

## Hard rules

- Never output dosing, administration or sourcing instructions for non-FDA-approved peptides. State known risks, flag interactions, and refer to a clinician or pharmacist.
- Use synthetic personas only. Never put a real person's health information in code, fixtures, commits, Kordi memories or Kordi messages.
- Every recommendation must carry a source, a source type, an evidence grade and the rule id that produced the grade.
- Classify expertise per claim and never by platform. A credentialed physician on YouTube can be an expert source; an out-of-field credential is flagged.
- Public ratings may change clarity and format only. They never change evidence grades, source tiers or safety rules.
- Judges run at temperature 0 and use a different model family from the plan generator.

## Engineering conventions

- Python 3.11, plain functions, few dependencies. Keep secrets in `.env`, never committed.
- Every LLM output that feeds code is JSON validated against a schema in `src/schemas.py`.
- Cache every HTTP response under `data/cache/` so the demo runs offline.
- Small commits with a one-line message naming the milestone, e.g. `M2: source classifier rules`.

## Collaboration

- Post decisions in the Kordi build group prefixed `[DECISION]`, bugs prefixed `[BUG]`, and ratings prefixed `[RATING]`. The trace export is parsed by these tags.
- When context from Kordi is missing, ask in the thread. Do not guess from older messages.
