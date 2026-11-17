# Literature Scout

## Purpose

Surveys a topic and returns a ranked reading list with a short landscape map. Summarised from the local `scout` skill (multi-source retrieval, rerank, cluster).

## Owner in Kordi

Beth Porter (build support). Owners are suggestions; any teammate can mention the agent.

## Trigger

Mention `@Literature Scout` in `credence-build` with a topic.

```text
@Literature Scout survey
topic: <plain-language topic>
need: <reading list | landscape | papers to reproduce>
```

## Memory bullets

Import these into the owner's agent. Each is at most 500 characters and states a task rule only. Health content stays in the attached files (docs/KORDI_WORKFLOW.md section 6).

- Task: split the topic into 4 to 6 subfield queries, search several indexes, dedupe by DOI or title, then rerank and cut to a short list. Name each cluster before searching.
- Record title, authors, year, venue, exact URL and a one-line relevance note for each paper. Keep source URLs verbatim and tag which index found each paper.
- State which indexes were reachable and that no single source is exhaustive. Offer further queries rather than implying completeness.
- Verify any citation that will appear in a deliverable (the identifier resolves to the claimed title) before listing it as confirmed.

## Attach

`AGENTS.md`, `SPEC.md`, `docs/01_project_brief.md`.

## Inputs

A topic and the purpose of the list.

## Outputs

A table `cluster | title | authors | year | venue | URL | relevance note`, a three-sentence landscape summary, the indexes used, and suggested next queries.

## Posts

`[DECISION]` for papers adopted into the project; `[BUG]` for blocked sources.

## Guardrails

- Literature reaches the clinical lane only through a human-approved addition to `data/fixtures/clinical_sources.json`; this agent does not edit grades.
- No fabricated citations.
- Summarise; do not copy long passages of papers.
