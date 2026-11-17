# Persona Twin

## Purpose

Predicts how one synthetic persona would react to a plan: predicted trust and whether they would act. The prompt and output schema are in `docs/06_trust_evaluation_loop.md` section 2; read it there, do not copy it.

## Owner in Kordi

Partner. Owners are suggestions; any teammate can mention the agent.

## Trigger

Mention `@Persona Twin` in the `credence-ratings` thread under a `[RESPONSE r-###]`.

```text
@Persona Twin rate
response: r-###
persona: p-002
```

## Memory bullets

Import these into the owner's agent. Each is at most 500 characters and states a task rule only. Health content stays in the attached files (docs/KORDI_WORKFLOW.md section 6).

- Task: follow the persona twin prompt in docs/06_trust_evaluation_loop.md section 2 exactly. Run at temperature 0, on a different model family from the plan generator.
- Use only the persona profile and the response text. Do not judge medical correctness; judge how this person would receive it.
- Return the JSON from that section only: predicted_trust 0 to 1, would_act_immediate, most_trusted_source, least_trusted_source, reason.
- Post the rating as a reply: [RATING r-###] role=twin format=hundred score=<0 to 100> act=<yes|not_yet|no>, then the reason.

## Attach

`AGENTS.md`, `SPEC.md`, `docs/06_trust_evaluation_loop.md`, the persona file under `data/fixtures/personas/`.

## Inputs

Persona JSON and the response text.

## Outputs

The JSON object defined in `docs/06_trust_evaluation_loop.md` section 2, followed by one `[RATING r-###] role=twin ...` reply line.

## Posts

`[RATING r-###]` in `credence-ratings`; `[BUG]` for invalid JSON.

## Guardrails

- Temperature 0; model family differs from the plan generator.
- Never sees the auditor's score or human ratings before rating.
- Twin fidelity is judged against the real user's rating, not assumed.
- Synthetic personas only; the demo persona is p-002 (synthetic: 42-year-old woman, 3 months semaglutide, no diabetes, considering BPC-157).
