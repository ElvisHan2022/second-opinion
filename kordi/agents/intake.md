# Intake Agent

## Purpose

Turns a spoken or typed intake transcript into a validated synthetic persona (goals, conditions, medications, risk tolerance 1 to 5, readiness to act 1 to 5, stated trust per source type). Implementation: `src/intake/persona.py` (`extract_persona`, `load_persona`).

## Owner in Kordi

Elvis. Owners are suggestions; any teammate can mention the agent.

## Trigger

Mention `@Intake Agent` in `credence-build` with a transcript id or a pasted synthetic transcript.

```text
@Intake Agent extract persona
transcript: <persona id such as p-002, or pasted synthetic transcript>
```

## Memory bullets

Import these into the owner's agent. Each is at most 500 characters and states a task rule only. Health content stays in the attached files (docs/KORDI_WORKFLOW.md section 6).

- Task: turn an intake transcript into one persona JSON that validates against the Persona schema in src/schemas.py. Return JSON only, no prose.
- If a field is missing from the transcript, set it to null and list it under missing_fields. Never invent a value to fill a gap.
- Risk tolerance and readiness to act are integers 1 to 5. Quote the transcript phrase that justifies each score in a rationale field.
- Use synthetic transcripts only. If a transcript looks like a real person, stop and post [BUG] saying so, without repeating the details.

## Attach

`AGENTS.md`, `SPEC.md`, `src/schemas.py`, `data/fixtures/personas/` (transcripts). `@`-reference the repo folder so the agent can run `src/intake/persona.py`.

## Inputs

A synthetic transcript (file under `data/fixtures/personas/` or pasted text).

## Outputs

One JSON object matching the Persona schema (`id`, `goals`, `conditions`, `medications`, `risk_tolerance`, `readiness_to_act`, trust by source type), plus `missing_fields` (list) and `rationale` (one line per scored field).

## Posts

`[MILESTONE M1]` when the extractor passes tests on a new transcript; `[BUG]` for schema failures or Kordi friction.

## Guardrails

- Synthetic personas only; the demo persona is p-002 (synthetic: 42-year-old woman, 3 months semaglutide, no diabetes, considering BPC-157).
- JSON validated against `src/schemas.py` before anything downstream reads it.
- Never copy health details of a real person into code, fixtures, memories or messages.
