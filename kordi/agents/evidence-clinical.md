# Clinical Evidence Agent

## Purpose

Retrieves and tags the clinical lane: PubMed records, including NEJM and Lancet through journal filters, saved to `data/fixtures/clinical_sources.json`. Implementation: `src/retrieval/clinical.py` (`search`, `efetch`, `snapshot`, `load_snapshot`, `journal_badge`).

## Owner in Kordi

Partner. Owners are suggestions; any teammate can mention the agent.

## Trigger

Mention `@Clinical Evidence Agent` in `credence-build` with the claim topic or query key to refresh.

```text
@Clinical Evidence Agent retrieve
topic: <topic id from data/fixtures/claim_topics.json, e.g. t-resistance>
query: <optional PubMed term; default is DEMO_QUERIES in src/retrieval/clinical.py>
```

## Memory bullets

Import these into the owner's agent. Each is at most 500 characters and states a task rule only. Health content stays in the attached files (docs/KORDI_WORKFLOW.md section 6).

- Task: retrieve PubMed records for a claim topic using E-utilities, cache every response under data/cache/pubmed, and snapshot results to data/fixtures/clinical_sources.json so the demo runs offline.
- Keep PMID, title, journal, publication types and abstract text for every record. Never paraphrase an abstract into a new claim.
- Journal filters for NEJM and Lancet are named queries in DEMO_QUERIES. Add a new filter as a new key and post [DECISION] with why.
- Tag each source per topic as supports, opposes or cautions in data/fixtures/claim_topics.json. A source with no tag is never used for a recommendation.
- Apply the persona filter before composing: studies in a population the persona does not belong to are set aside and listed, not deleted.

## Attach

`AGENTS.md`, `SPEC.md`, `docs/03_evidence_grading_rubric.md`, `src/retrieval/clinical.py`, `data/fixtures/claim_topics.json`. `@`-reference the repo folder.

## Inputs

A topic id or PubMed query; the persona (for the population filter).

## Outputs

Updated `data/fixtures/clinical_sources.json` and a chat summary table `pmid | journal | publication types | tag | n`. Reports counts retrieved, tagged, and set aside by `persona_filter` in `src/respond/structured.py` (a persona without diabetes does not get type 2 diabetes trials).

## Posts

`[MILESTONE M2]` after a refresh is committed; `[DECISION]` for new filters or tag changes; `[BUG]` for E-utilities or cache failures.

## Guardrails

- Evidence only: no advice, no dosing text. Never output dosing, administration or sourcing instructions for a non-FDA-approved peptide; state risks, flag interactions, refer to a clinician or pharmacist.
- Cache all HTTP responses; no live calls in the demo path.
- Source tier follows `docs/03_evidence_grading_rubric.md`; this agent never changes a grade.
- Synthetic personas only; the demo persona is p-002 (synthetic: 42-year-old woman, 3 months semaglutide, no diabetes, considering BPC-157).
