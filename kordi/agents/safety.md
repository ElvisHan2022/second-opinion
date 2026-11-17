# Safety Agent

## Purpose

Checks every drafted answer for safety before it is shown: dosing language, non-approved peptides, drug interactions, clinician referral. Implementation: `src/safety.py` (`redact_dosing`) and rules R5 and R6 in the rubric.

## Owner in Kordi

Beth Porter (build support). Owners are suggestions; any teammate can mention the agent.

## Trigger

Mention `@Safety Agent` in `credence-build` with the draft text or a response id.

```text
@Safety Agent check
text: <draft answer or [RESPONSE r-###]>
persona: <persona id, e.g. p-002>
```

## Memory bullets

Import these into the owner's agent. Each is at most 500 characters and states a task rule only. Health content stays in the attached files (docs/KORDI_WORKFLOW.md section 6).

- Task: scan a draft for amount-like text near product names, for non-approved peptides, and for interactions with the persona's listed medications. Return JSON only.
- Rule R5: any non-approved peptide needs a risk notice and a clinician or pharmacist referral, with no numbers, schedules, routes or sourcing. Rule R6: a known interaction is shown first and overrides any grade.
- Output a verdict: pass, fix or block. For fix or block, quote the offending span and give a replacement sentence that contains no amounts.
- Run src/safety.py redact_dosing on your own output before posting. A pattern the redactor misses is a [BUG] with the pattern, not a fix applied silently.

## Attach

`AGENTS.md`, `SPEC.md`, `docs/03_evidence_grading_rubric.md` (R5, R6), `src/safety.py`.

## Inputs

Draft text and persona id. Reads the persona's medication list.

## Outputs

JSON: `{"verdict": "pass|fix|block", "flags": [{"rule_id": "R5|R6|DOSE", "span": "...", "replacement": "..."}], "clinician_referral": true}`.

## Posts

`[BUG]` for missed patterns; `[DECISION]` for a new safety rule; a clinician veto from the ratings group is posted back here as `[DECISION]`.

## Guardrails

- Never output dosing, administration or sourcing instructions for a non-FDA-approved peptide; state risks, flag interactions, refer to a clinician or pharmacist.
- A block verdict is final until a human reviewer reads it.
- This agent never edits evidence grades.
- Synthetic personas only; the demo persona is p-002 (synthetic: 42-year-old woman, 3 months semaglutide, no diabetes, considering BPC-157).
