# SPEC.md: Credence MVP build spec

Build window: about 3:15 PM to 6:15 PM, Nov 16 2026. Demo at 6:30 PM. Read `AGENTS.md` first.

## 1. What the demo must show

One synthetic GLP-1 user goes from intake to a graded plan, and four raters score the plan:

1. Intake transcript becomes a persona (JSON).
2. One user question is answered from two evidence lanes, clinical and public.
3. Each source is classified (expert category) and graded (tier and rule id).
4. A plan with three horizons: immediate action, next action, longer term.
5. Ratings from the user, the persona twin, the evidence auditor and at least two human stakeholders collected in Kordi.
6. A calibration chart (warranted trust on x, user trust on y) and one medicine-versus-public disagreement shown with its Kordi trace.

Anything else is out of scope today.

## 2. Repository layout

```
AGENTS.md  CLAUDE.md  SPEC.md  README.md
docs/                     project brief, rubric, trust loop, Kordi workflow, bug log
data/fixtures/
  personas/               synthetic intake transcripts (.txt) and personas (.json)
  public_posts.json       hand-collected public posts (Reddit, X, Instagram, TikTok)
  kordi_traces/           exported kordi-trace-*.jsonl files
data/cache/               cached HTTP responses
src/
  schemas.py              JSON schemas and dataclasses for every object below
  intake/persona.py       transcript -> persona JSON
  retrieval/clinical.py   PubMed (E-utilities) and medRxiv search, cached
  retrieval/public.py     load public_posts.json; optional Reddit search
  classify/expert.py      expert category per (speaker, claim)
  grade/evidence.py       tier assignment and rules R1 to R6
  plan/generate.py        graded evidence + persona -> three-horizon plan
  judges/twin.py          persona twin judge
  judges/auditor.py       evidence auditor judge
  eval/kordi_trace.py     parse Kordi trace export -> ratings table
  eval/metrics.py         twin fidelity, calibration gap, medicine-vs-public gap
app/streamlit_app.py      demo UI
tests/                    pytest checks in section 6
```

## 3. Data objects (`src/schemas.py`)

- **Persona**: `user_id`, `goals[]`, `conditions[]`, `medications[]` (name, approved), `supplements_peptides[]`, `risk_tolerance` 1 to 5, `readiness_to_act` 1 to 5, `source_trust` {doctor, physician_creator, coach, reddit, influencer: 1 to 5}.
- **Source**: `id`, `lane` (clinical | public), `title`, `url`, `speaker`, `speaker_credential`, `platform`, `cites_evidence` (bool), `coi` (yes | no | unknown), `text`.
- **ClassifiedSource**: Source + `expert_category` (expert_evidence | expert_opinion | relayed_evidence | anecdote) + `out_of_field` (bool) + `tier` (A to E).
- **GradedClaim**: `claim`, `sources[]`, `grade` (Strong | Moderate | Limited | Excluded), `rule_id`, `safety_flags[]`.
- **Plan**: `immediate`, `next`, `longer_term`, each a list of {action, grade, rule_id, source_ids, pros, cons}; plus `medical_vs_public` {agree[], split[] with explanation}.
- **Rating**: `response_id`, `rater_id`, `rater_role` (user | twin | auditor | physician | nurse | dietitian | engineer | public), `format` (thumbs | stars5 | ten | hundred | text), `raw`, `score_0_1`, `would_act` (yes | not_yet | no | null), `dimensions` {D1..D7: 0 to 2} (auditor and clinicians), `kordi_message_id`.

## 4. Component rules

**Intake.** Use the ElevenLabs agent transcript if available; otherwise a typed transcript in `data/fixtures/personas/`. One LLM call extracts the persona JSON; validate against the schema.

**Clinical lane.** PubMed E-utilities (`esearch` then `esummary`/`efetch` abstracts) and medRxiv API. Top 5 results per query. UpToDate, NEJM, Lancet and OpenEvidence are listed as future licensed sources; do not scrape them.

**Public lane.** `public_posts.json` with 10 to 20 hand-collected posts on the demo question, including at least one credentialed creator (for example Doctor Mike), one coach and one influencer. Record speaker credential, platform, whether evidence is cited, and conflicts of interest as observed.

**Expert classifier (deterministic).**

| Credentialed for this claim | Cites evidence | Category |
| --- | --- | --- |
| yes | yes | expert_evidence |
| yes | no | expert_opinion |
| no | yes | relayed_evidence |
| no | no | anecdote |

A credential counts only within its field; otherwise set `out_of_field = true` and treat as not credentialed. Platform is never an input. Lived experience posts are labeled anecdote and are valid evidence for tolerability and adherence, not efficacy.

**Grading.** Tiers and rules R1 to R6 exactly as in `docs/03_evidence_grading_rubric.md`. R5 (non-approved peptide) and R6 (interaction) always run.

**Plan generation.** One LLM call receives the persona and graded claims only. It may not introduce claims that are not in the graded list. Risk tolerance below 3 hides Limited options. Output validated against the Plan schema; any dosing language for a non-approved peptide fails validation and triggers a regeneration with the safety rule restated.

**Judges.** Prompts verbatim from `docs/06_trust_evaluation_loop.md`. Temperature 0, different model family from the generator. Log model name and rubric version with every score.

**Kordi ratings.** Each plan is posted to the Kordi ratings group as one message ending with a response id, e.g. `[RESPONSE r-001]`. Raters reply with `[RATING r-001] role=<role> format=<format> score=<value> act=<yes|not_yet|no>` plus optional free text. `src/eval/kordi_trace.py` parses the exported JSONL (`schema: kordi.session-trace`, message lines with `sender`, `text`, `reply_to`, `timestamp`) into Rating rows. Free-text ratings are coded to 0 to 1 by the auditor model with the raw text kept.

**Metrics.** Twin fidelity = mean absolute difference and agreement on `would_act` between twin and user. Calibration gap = user score minus auditor `warranted_trust`. Medicine-versus-public gap = mean clinician score minus mean public score per response. Report n beside every number.

## 5. Milestones

| Time | Milestone | Done when |
| --- | --- | --- |
| 3:15 to 3:40 | M0 Setup | Repo cloned, `.env` set, Kordi build and ratings groups created, docs attached, AGENTS.md imported |
| 3:40 to 4:20 | M1 Data | One synthetic persona JSON, 10 to 20 public posts, cached PubMed results for the demo question |
| 4:20 to 5:00 | M2 Classify and grade | Every source classified and graded with rule ids; tests in section 6 pass |
| 5:00 to 5:30 | M3 Plan and judges | Three-horizon plan, twin and auditor scores produced |
| 5:30 to 5:50 | M4 Ratings in Kordi | Plan posted, at least 2 stakeholder and 1 user rating collected, trace exported and parsed |
| 5:50 to 6:15 | M5 Demo | Streamlit page shows plan, four ratings, calibration chart, one disagreement; bug log complete |

Fallback at 5:00: if live retrieval or voice fails, run entirely from cached fixtures and say so in the demo.

## 6. Acceptance checks (`tests/`)

1. Classifier: four fixture sources land in the four categories; an out-of-field credential is flagged.
2. Platform independence: the same claim and speaker produce the same category on YouTube and in a journal.
3. Safety: any plan mentioning a non-approved peptide contains the R5 notice and no dosing pattern (numbers followed by mg, mcg, units or IU near the peptide name).
4. Tier E only: a claim supported only by Tier E sources never appears as a recommendation.
5. Determinism: the same persona and cached sources produce the same grades twice.
6. Trace parser: a fixture `kordi-trace` file with three `[RATING]` replies yields three Rating rows with correct roles and scores.
7. Feedback routing: a public rating cannot change any grade or tier.

## 7. Out of scope today

Real wearable ingestion, telehealth handoff, payments, authentication, real patient data, scraping paywalled journals.
