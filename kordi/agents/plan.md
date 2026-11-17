# Plan Agent

## Purpose

Builds the three-horizon plan (immediate action, next action, longer term) from the persona and graded claims only. Spec: `SPEC.md`, plan generation. Planned implementation: `src/plan/generate.py`.

## Owner in Kordi

Elvis. Owners are suggestions; any teammate can mention the agent.

## Trigger

Mention `@Plan Agent` in `credence-build` with a persona id and the composed topics.

```text
@Plan Agent plan
persona: p-002
claims: <topic ids, or all composed topics>
```

## Memory bullets

Import these into the owner's agent. Each is at most 500 characters and states a task rule only. Health content stays in the attached files (docs/KORDI_WORKFLOW.md section 6).

- Task: write a plan with immediate, next and longer_term lists. Each item has action, grade, rule_id, source_ids, pros and cons. Use only claims in the graded list; never introduce a new claim.
- Respect risk tolerance: below 3, show only Strong and Moderate options. At 3 or above, Limited options appear with a caution label. Risk tolerance never changes safety flags.
- Match the horizon to readiness to act: low readiness gets education first and fewer options. Keep the three horizons distinct and proportionate to the evidence.
- Add medical_vs_public with agree and split lists, each split explained in one sentence from the composed topics.
- Output is validated against the Plan schema. If the Safety Agent returns fix or block, regenerate with the rule restated; do not patch by hand.

## Attach

`AGENTS.md`, `SPEC.md`, `docs/03_evidence_grading_rubric.md`, `docs/06_trust_evaluation_loop.md`, `src/schemas.py`.

## Inputs

Persona JSON and the graded, composed topics from the Response Composer.

## Outputs

Plan JSON per `SPEC.md`: `immediate`, `next`, `longer_term` (lists of `{action, grade, rule_id, source_ids, pros, cons}`) and `medical_vs_public` (`{agree[], split[]}`). Then a short readable version ending with `[RESPONSE r-###]`.

## Posts

`[RESPONSE r-###]` to `credence-ratings` after a Safety Agent pass; `[DECISION]` for horizon or option-set rules.

## Guardrails

- Every recommendation carries source, source type, grade and rule id.
- Never output dosing, administration or sourcing instructions for a non-FDA-approved peptide; state risks, flag interactions, refer to a clinician or pharmacist.
- Judges and the plan generator must be different model families; this agent never scores its own plan.
- Synthetic personas only; the demo persona is p-002 (synthetic: 42-year-old woman, 3 months semaglutide, no diabetes, considering BPC-157).
