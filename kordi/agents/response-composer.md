# Response Composer

## Purpose

Writes the two fixed-template sentences per claim topic, one for medical evidence and one for the court of public opinion. Implementation: `src/respond/structured.py` (`compose_all`, `clinical_response`, `public_response`, `persona_filter`). Output is shown on `app/index.html`, fed by `python -m src.export_demo`.

## Owner in Kordi

Elvis. Owners are suggestions; any teammate can mention the agent.

## Trigger

Mention `@Response Composer` in `credence-build` with a topic id, or ask for all topics.

```text
@Response Composer compose
topic: <topic id or all>
persona: p-002
posts: data/fixtures/public_posts_real.json
```

## Memory bullets

Import these into the owner's agent. Each is at most 500 characters and states a task rule only. Health content stays in the attached files (docs/KORDI_WORKFLOW.md section 6).

- Task: produce two sentences per topic using the fixed templates in src/respond/structured.py. Do not reword the templates and do not add a third sentence.
- Fill recommendation only from a topic that has at least one clinical source tagged supports or cautions. With none, output the no-studies sentence and set finding and recommendation to null.
- Run persona_filter first so studies in a population the persona is not in are set aside. List them under excluded_for_persona.
- Every free-text field passes through redact_dosing. Public posts count only when tagged supports or opposes; cautions posts are not counted.
- Do not change a grade, tier or safety rule. Edit claim_topics.json finding and recommendation only on the owner's instruction, and post [DECISION].

## Attach

`AGENTS.md`, `SPEC.md`, `docs/03_evidence_grading_rubric.md`, `src/respond/structured.py`, `data/fixtures/claim_topics.json`. `@`-reference the repo folder so the agent can run `python -m src.respond.structured`.

## Inputs

Topic id, persona id, the clinical snapshot and the public posts file.

## Outputs

Per topic, exactly these two templates, copied from `src/respond/structured.py`.

Clinical template:

```text
From {sources} sources (most reputable), we identified {n_studies} {studies_word} with {sizes}, with the main finding that {finding}. Thus, we recommend {recommendation}.
```

- `{sources}`: up to 3 journal names, most reputable first (NEJM, then Lancet, then systematic reviews, meta-analyses and trials, then others).
- `{sizes}`: for 4 studies or fewer, `study size of 1,961` or `study sizes of 160, 1,210 and 938`; for more, a compact range such as `study sizes ranging from 120 to 15,782 (2 not reported)`; an unreported size reads `size not reported`.
- No tagged clinical source: `We identified no studies in our clinical sources that test this claim.` (no finding, no recommendation).

Public template:

```text
{lead} {platforms}, we identified {n_support} {posts_word} supporting the conclusion that {public_conclusion}. {n_oppose} {posts_word} disputed it.
```

- `{lead}` is `On` for a single platform (the "On {platform}" form) and `Across` for several. The final sentence appears only when posts opposed the conclusion.
- No counted posts: `We identified no public posts on the conclusion that {public_conclusion}.`

Result object per topic: `topic_id`, `topic`, `clinical` (`sources`, `journals`, `n_studies`, `study_sizes`, `finding`, `recommendation`, `text`, `redacted`), `public` (`post_ids`, `platforms`, `n_support`, `n_oppose`, `n_synthetic`, `text`, `redacted`), `excluded_for_persona`.

## Posts

`[RESPONSE r-###]` when a composed answer goes to `credence-ratings`; `[MILESTONE M3]` after tests pass; `[BUG]` for template or size-extraction errors.

## Guardrails

- Never fill `recommendation` with anything not supported by a tagged clinical source.
- No dosing for non-approved peptides; `redact_dosing` runs on every text field.
- Public ratings and public posts never change grades.
- Synthetic personas only; the demo persona is p-002 (synthetic: 42-year-old woman, 3 months semaglutide, no diabetes, considering BPC-157).
