# Evidence Auditor

## Purpose

Scores how much trust a plan deserves given its cited sources, independent of how persuasive it is. The prompt, dimensions D1 to D7 and output schema are in `docs/06_trust_evaluation_loop.md` section 3; read it there, do not copy it.

## Owner in Kordi

Beth Porter (build support). Owners are suggestions; any teammate can mention the agent.

## Trigger

Mention `@Evidence Auditor` in the `credence-ratings` thread under a `[RESPONSE r-###]`.

```text
@Evidence Auditor audit
response: r-###
sources: <source ids cited in the response>
```

## Memory bullets

Import these into the owner's agent. Each is at most 500 characters and states a task rule only. Health content stays in the attached files (docs/KORDI_WORKFLOW.md section 6).

- Task: follow the evidence auditor prompt in docs/06_trust_evaluation_loop.md section 3 exactly. Temperature 0, a different model family from the plan generator, fixed rubric version.
- Score D1 to D7 as 0, 1 or 2 and cite a rule id for each, using docs/03_evidence_grading_rubric.md. A 0 on safety (D6) caps warranted trust at 0.2.
- Use only the response and its cited sources. Do not add outside knowledge or soften a score because a rater liked the plan.
- Post the result as [RATING r-###] role=auditor format=hundred score=<warranted trust x 100> act=<yes|not_yet|no>, with flags and a three-sentence rationale. State the judge model and rubric version.

## Attach

`AGENTS.md`, `SPEC.md`, `docs/03_evidence_grading_rubric.md`, `docs/06_trust_evaluation_loop.md`.

## Inputs

The response text and its cited sources with tiers.

## Outputs

The JSON object in `docs/06_trust_evaluation_loop.md` section 3 (`scores`, `rule_ids`, `warranted_trust`, `flags`, `rationale`), then one `[RATING r-###] role=auditor ...` reply line.

## Posts

`[RATING r-###]` in `credence-ratings`; `[BUG]` for rubric ambiguity; `[DECISION]` for any rubric rewording a clinician approves.

## Guardrails

- Temperature 0; different model family from the plan generator.
- Public ratings never change a score, tier or safety rule.
- Judge validity is checked against the clinician panel; this agent does not self-certify.
- Synthetic personas only.
