# NEJM/Lancet Sources, Evidence Ring and Kordi Agents Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add NEJM and Lancet papers via PubMed, a per-claim expert classifier, a structured response composer (clinical and public templates), a static "Second Opinion" demo page with a medicine-vs-public ring, and one Kordi agent file per agent.

**Architecture:** Python modules produce validated `Source`s (`src/schemas.py`). `src/export_demo.py` classifies them and writes `app/demo_data.js` (`window.DEMO = {...}`). `app/index.html` renders it with no server and no network.

**Tech Stack:** Python 3.11 stdlib + pytest (`.venv`), vanilla HTML/CSS/JS, inline SVG.

**Spec:** `docs/superpowers/specs/2026-11-16-sources-ring-kordi-agents-design.md`

## Global Constraints

- Never output dosing, administration or sourcing instructions for non-FDA-approved peptides (AGENTS.md).
- Classify expertise per claim and never by platform (AGENTS.md).
- Synthetic personas only; no real person's health information.
- Cache every HTTP response under `data/cache/`; the demo runs offline from committed fixtures.
- Python 3.11, plain functions, few dependencies; run `.venv/Scripts/python -m pytest -q` before each commit.
- No OpenEvidence code; no scraping NEJM, Lancet or any journal site (PubMed E-utilities only); no copied brand logos; no invented institutional sources.
- Commit messages name the milestone, e.g. `M2: expert classifier`.

## Review Focus

1. A query returning zero PubMed ids: `efetch([])` returns `[]` with no HTTP call, and the snapshot still writes. (Task 2 test `test_efetch_empty_makes_no_request`)
2. A source whose credential field is missing from the coverage map, or whose `claim_field` is None, is treated as out of field and raises no KeyError. (Task 1 test `test_unknown_fields_are_out_of_field`)
3. Any exported text (post, abstract, claim, recommendation) containing dosing near a non-approved peptide is redacted before it reaches the page. (Task 3 `test_redact_dosing`, Task 4 `test_no_peptide_dosing_in_export`)
4. Text containing quotes or `</script>` in `demo_data.js` is JSON-encoded so the page still parses. (Task 4 test `test_demo_js_escapes_script_close`)
5. A clinical source with an unrecognised journal still gets a badge ("PubMed") and is not dropped. (Task 2 test `test_journal_badge`)

---

### Task 1: Expert classifier (`M2: expert classifier`)

**Files:**
- Create: `src/classify/__init__.py`, `src/classify/expert.py`
- Test: `tests/test_classify_expert.py`

**Interfaces:**
- Produces: `COVERAGE: dict[str, set[str]]` (credential field -> claim fields it covers; every field also covers itself), `covers(credential_field: str | None, claim_field: str | None) -> bool`, `classify_expert(source: Source) -> tuple[str, bool]` returning `(expert_category, out_of_field)`.

Rules: clinical lane -> `("expert_evidence", False)`. Public lane: credentialed = `speaker_credential` present and `covers(...)`; `out_of_field` = credential present and not covered; then the SPEC table on (credentialed, `cites_evidence`). Platform is never read. Coverage (builder may extend): internal medicine -> obesity medicine, primary care; primary care -> obesity medicine; obesity medicine -> nutrition, exercise science; sports medicine -> exercise science; chiropractic and personal training cover only themselves.

- [ ] **Step 1: Write failing tests** in `tests/test_classify_expert.py`:
  - `test_four_categories_from_fixture`: `pub-01` -> expert_evidence, `pub-02` -> expert_opinion, `pub-08` -> relayed_evidence, `pub-07` -> anecdote (SPEC check 1).
  - `test_out_of_field_flagged`: `pub-04` -> `("relayed_evidence", True)`; `pub-05` out_of_field True.
  - `test_platform_independence`: `dataclasses.replace(pub_01, platform=p)` for p in YouTube, journal, TikTok all give the same result (SPEC check 2).
  - `test_unknown_fields_are_out_of_field`: credential "MD", `credential_field="dermatology"`, `claim_field=None` -> out_of_field True, category in {relayed_evidence, anecdote}.
  - `test_clinical_sources_are_expert_evidence`: every `clinical.load_snapshot()` source -> `("expert_evidence", False)`.
- [ ] **Step 2:** Run `.venv/Scripts/python -m pytest tests/test_classify_expert.py -q`; expect an import failure.
- [ ] **Step 3:** Implement `src/classify/expert.py` per the interfaces.
- [ ] **Step 4:** Run the full suite; expect all to pass.
- [ ] **Step 5:** Commit `M2: expert classifier with credential coverage map`.

### Task 2: NEJM and Lancet via PubMed (`M1: NEJM and Lancet sources`)

**Files:**
- Modify: `src/schemas.py` (add `journal: str | None = None`, `journal_abbrev: str | None = None` to `Source`; read both in `validate_source`)
- Modify: `src/retrieval/clinical.py` (add query key `nejm_lancet`; fill `journal` from `Journal/Title` and `journal_abbrev` from `MedlineTA`; add `journal_badge`)
- Regenerate: `data/fixtures/clinical_sources.json`
- Test: `tests/test_m1_data.py` (extend)

**Interfaces:**
- Produces: `DEMO_QUERIES["nejm_lancet"]` = the lean-mass and exercise terms ANDed with `("N Engl J Med"[ta] OR "Lancet"[ta] OR "Lancet Diabetes Endocrinol"[ta])`; `journal_badge(source: Source) -> str` returning `"NEJM"` for abbrev `N Engl J Med`, `"Lancet"` for an abbrev starting with `Lancet`, else `"PubMed"`.

- [ ] **Step 1: Write failing tests**:
  - `test_snapshot_includes_nejm_or_lancet`: at least one snapshot source with `journal_badge` in {"NEJM", "Lancet"}.
  - `test_clinical_sources_have_journal_fields`: every clinical source has non-empty `journal` and `journal_abbrev`.
  - `test_journal_badge`: abbrevs `N Engl J Med` -> NEJM, `Lancet Diabetes Endocrinol` -> Lancet, `Obesity (Silver Spring)` -> PubMed, None -> PubMed.
  - `test_efetch_empty_makes_no_request`: monkeypatch `clinical._get` to raise; `efetch([]) == []`.
- [ ] **Step 2:** Run; expect failure.
- [ ] **Step 3:** Implement; run `python -m src.retrieval.clinical` live to refresh and cache the snapshot.
- [ ] **Step 4:** Run the full suite (including the existing no-dosing fixture test); expect all to pass.
- [ ] **Step 5:** Commit `M1: NEJM and Lancet sources via PubMed`.

### Task 3: Structured response composer (`M3: structured response composer`)

Added 15:55 at Elvis's request. Produces the two fixed-template sentences per claim topic; an LLM may later fill `finding`/`recommendation`, but today they are hand-written in the fixture.

**Files:**
- Create: `data/fixtures/claim_topics.json`, `src/safety.py`, `src/respond/__init__.py`, `src/respond/structured.py`
- Test: `tests/test_structured_response.py`

`claim_topics.json`: `{"_note": "...hand-tagged; replace finding/recommendation with M3 generator output later", "topics": [...]}`. Each topic: `{id, topic, finding, recommendation, public_conclusion, stances: {source_id: "supports"|"opposes"|"cautions"}}`. Topics (ids fixed): `t-resistance` (resistance training preserves muscle), `t-protein` (prioritise protein), `t-leanmass` (GLP-1 lean-mass loss is meaningful), `t-bpc-muscle` (BPC-157 helps muscle on a GLP-1), `t-bpc-safety` (BPC-157 safety and regulatory status), `t-collagen` (collagen prevents muscle loss). Stances cover both public post ids (`pub-01`..`pub-16`) and clinical ids (`pmid-*` from `data/fixtures/clinical_sources.json`); read each source before tagging it. The `t-bpc-muscle` recommendation must say not to start BPC-157 without a clinician, that it is not FDA-approved, and must contain no dose.

**Templates (exact copy):**
- Clinical: `From {sources} sources (most reputable), we identified {n_studies} {studies_word} with study sizes of {sizes}, with the main finding that {finding}. Thus, we recommend {recommendation}.`
- Public: `Across {platforms}, we identified {n_support} {posts_word} supporting the conclusion that {public_conclusion}.` plus, when `n_oppose > 0`, ` {n_oppose} {posts_word2} disputed it.`
- Lists join as `A`, `A and B`, `A, B and C`. Sizes print with thousands separators; a study without a detectable size prints `size not reported`. `{sources}` lists at most 3 distinct journal names, most reputable first: NEJM, then Lancet journals, then others in tier order (systematic review/meta-analysis/RCT before other types), ties alphabetical.

**Interfaces:**
- Consumes: `clinical.load_snapshot()`, `clinical.journal_badge(source)` (Task 2), `public.load_posts()`; `Source.journal`, `Source.publication_types`, `Source.synthetic`.
- Produces:
  - `src/safety.py`: `NON_APPROVED_PEPTIDES: list[str]` (`["BPC-157", "BPC 157", "TB-500", "ipamorelin", "CJC-1295"]`), `DOSE_PATTERN: re.Pattern` (number + mg|mcg|µg|μg|ug|unit(s)|IU, case-insensitive), `redact_dosing(text: str) -> tuple[str, bool]` replacing each sentence with a dose pattern within 120 chars of a non-approved peptide name by `[removed: dosing for a non-approved peptide]`.
  - `src/respond/structured.py`: `load_topics() -> list[dict]`; `extract_study_size(text: str) -> int | None` (largest of: `n = 1,234` / `N=123` / `(n=123)`, and `<int> participants|patients|adults|subjects|individuals|people|women|men|volunteers`; numbers ≥ 5 only); `clinical_response(topic: dict, sources: list[Source]) -> dict` with keys `topic_id, sources, n_studies, study_sizes (list[int|None]), finding, recommendation, text`, using only clinical sources whose stance is `supports` or `cautions`; `public_response(topic: dict, posts: list[Source]) -> dict` with keys `topic_id, platforms, n_support, n_oppose, n_synthetic, public_conclusion, text`; `compose_all() -> list[dict]` returning `{topic_id, topic, clinical, public}` per topic. Every `text` passes through `redact_dosing`; a redaction sets `redacted: True`.

- [ ] **Step 1: Write failing tests** in `tests/test_structured_response.py`:
  - `test_extract_study_size`: `"randomized 1,961 adults"` -> 1961; `"(n = 304)"` -> 304; `"N=12 and 2,539 participants"` -> 2539; `"a review of trials"` -> None; `"in 3 patients"` -> None.
  - `test_clinical_template_exact`: for a hand-built topic and two fake Sources (journals `N Engl J Med` RCT with "1,961 adults", `Obesity` review with no size), text equals `From N Engl J Med and Obesity sources (most reputable), we identified 2 studies with study sizes of 1,961 and size not reported, with the main finding that X. Thus, we recommend Y.` (use the journal names as stored; badge ordering puts NEJM first).
  - `test_public_template_exact`: fake posts on Reddit (supports), TikTok (supports), Instagram (opposes) -> `Across Reddit, TikTok and Instagram, we identified 2 posts supporting the conclusion that Z. 1 post disputed it.` (platform order = first appearance).
  - `test_singular_words`: one study -> `1 study`, one post -> `1 post`.
  - `test_recommendations_never_contain_peptide_dosing`: for every topic in `compose_all()`, no `DOSE_PATTERN` match within 120 chars of a peptide name in either `text`.
  - `test_bpc_topic_refers_to_clinician`: `t-bpc-muscle` clinical text contains "clinician" or "prescriber" and "not FDA-approved".
  - `test_redact_dosing`: `"Some use BPC-157 at 250 mcg daily. Lift weights."` -> dosing sentence replaced, `Lift weights.` kept, flag True; `"Semaglutide 2.4 mg weekly."` -> unchanged, False.
  - `test_public_counts_synthetic_posts`: `n_synthetic` equals the number of counted posts with `synthetic` True.
- [ ] **Step 2:** Run; expect failure.
- [ ] **Step 3:** Implement and write `claim_topics.json`.
- [ ] **Step 4:** Run the full suite; all pass. Print `compose_all()` texts and paste them into the report.
- [ ] **Step 5:** Commit `M3: structured response composer`.

### Task 4: Demo data export (`M5: demo data export`)

**Files:**
- Create: `src/export_demo.py`
- Test: `tests/test_export_demo.py`

**Interfaces:**
- Consumes: `load_persona`, `load_posts`, `clinical.load_snapshot`, `clinical.journal_badge`, `classify_expert` (Task 1), `safety.redact_dosing`, `structured.load_topics`, `structured.compose_all` (Task 3).
- Produces: `corner(category: str) -> str` ("medicine" for expert_evidence/expert_opinion, else "public"); `topic_verdict(topic: dict, corner_by_id: dict[str, str]) -> dict` with `{id, topic, medicine: stance|None, public: stance|None, verdict: "agree"|"split"|"one-sided"}` using the majority stance per corner (ties -> "cautions"); `build_demo_data() -> dict` with keys `product` ("Second Opinion"), `synthetic` (True), `question`, `persona`, `fighters[]`, `topics[]` (verdict merged with that topic's `clinical` and `public` responses), `counts{medicine, public}`; `write_demo_js(path: Path = Path("app/demo_data.js")) -> Path` writing `window.DEMO = <json>;` with `</` escaped as `<\/`. Each fighter: `{id, lane, corner, expert_category, out_of_field, speaker, credential, platform, badge, coi, claim, title, url, text, synthetic}`; `badge` = `journal_badge` for clinical, platform for public; clinical `claim` = title; `text` redacted.

- [ ] **Step 1: Write failing tests**:
  - `test_corner_follows_classification_not_platform`: `pub-11` and `pub-01` -> medicine; `pub-04` -> public.
  - `test_topic_verdicts`: `t-resistance` -> "agree"; `t-bpc-muscle` -> "split".
  - `test_demo_js_escapes_script_close`: monkeypatch one fighter claim to contain `</script>` -> written file has no literal `</script>`; payload `json.loads` round-trips.
  - `test_build_demo_data_shape`: counts sum to fighters; `synthetic` True; corners ⊂ {medicine, public}; at least one badge in {NEJM, Lancet}; every topic has `clinical.text` and `public.text`.
  - `test_no_peptide_dosing_in_export`: `json.dumps(build_demo_data())` has no dose pattern within 120 chars of a peptide name.
- [ ] **Step 2:** Run; expect failure.
- [ ] **Step 3:** Implement.
- [ ] **Step 4:** Full suite passes; run `python -m src.export_demo` to write `app/demo_data.js`.
- [ ] **Step 5:** Commit `M5: demo data export` (include `app/demo_data.js`).

### Task 5: Demo page `app/index.html` (`M5: demo page with evidence ring`)

**Files:**
- Create: `app/index.html` (single file: HTML, CSS, JS; loads `demo_data.js` via `<script src>`)

**Requirements:** OpenEvidence-style layout without its branding: header "Second Opinion" with "Synthetic demo · not medical advice"; large read-only question box; persona chip row; **answer card** listing each topic with two labelled blocks, "Medical evidence" (the clinical template sentence) and "Court of public opinion" (the public template sentence), a verdict pill (agree/split/one-sided), and citation chips linking to references; a visible note when counted posts are synthetic placeholders; references list with NEJM/Lancet/PubMed badges and category chips. **Ring section**: square ring drawn in CSS/SVG with ropes and two corners labeled Medicine and Public, fighter cards (glyph icon, speaker, credential, badge, category chip, COI and out-of-field tags) placed in their corner; click opens a detail drawer with claim, text and link; scorecard listing topics with medicine stance, public stance and verdict. Light and dark via `prefers-color-scheme`; works from `file://`; no external requests; phone width without horizontal scroll.

- [ ] **Step 1:** Build the page.
- [ ] **Step 2:** Self-check by opening the file in a headless check or by reading DOM-free logic; the controller verifies in the browser pane (no console errors; per-corner counts equal `DEMO.counts`; `pub-11` in Medicine; `t-bpc-muscle` shows "split"; no dosing in page text; mobile width has no horizontal scroll).
- [ ] **Step 3:** Commit `M5: demo page with evidence ring`.

### Task 6: Kordi agent files (`docs: Kordi agent files`)

Changed 15:55: one markdown file per agent, ready to attach in the Kordi channel.

**Files:**
- Create: `kordi/agents/README.md` (index table: agent, file, owner, trigger; how to use in Kordi: attach file to `credence-build`, import its Memory bullets into the owner's agent, `@`-reference the repo folder, mention to trigger; tags from `docs/KORDI_WORKFLOW.md` §3)
- Create one file each: `kordi/agents/intake.md`, `evidence-clinical.md`, `public-opinion.md`, `safety.md`, `response-composer.md`, `plan.md`, `persona-twin.md`, `evidence-auditor.md`, `referee.md`, `shah-audit.md`, `literature-scout.md`, `code-review.md`
- Modify: `docs/KORDI_WORKFLOW.md` (one line under §1 Setup pointing to `kordi/agents/README.md`)

**Each file has exactly these sections:** `# <Agent name>`, `Purpose`, `Owner in Kordi`, `Trigger` (mention + message format in a code block), `Memory bullets` (each ≤500 chars; task rules only, no health content per KORDI_WORKFLOW §6), `Attach`, `Inputs`, `Outputs` (exact format), `Posts` (tags), `Guardrails`.

**Agent-specific content:**
- `response-composer.md`: outputs the two templates from Task 3 verbatim and names `src/respond/structured.py` as the implementation; it never fills `recommendation` with anything not supported by a graded claim.
- `public-opinion.md`: method today is Google search in Chrome (Claude in Chrome or a person) with site filters, e.g. `site:reddit.com`, `site:tiktok.com`, `site:instagram.com`, blogs; records each post into `data/fixtures/public_posts.json` shape (id, platform, url, speaker type, credential, credential_field, claim, claim_field, cites_evidence, coi, short paraphrase in `text`, `synthetic: false`); no quotes over 15 words, no private accounts, no personal health details of posters; later replaced by an API. Output is the public template sentence.
- `evidence-auditor.md` and `persona-twin.md`: point to the prompts in `docs/06_trust_evaluation_loop.md` (do not copy them), temperature 0, different model family from the plan generator.
- `referee.md`, `shah-audit.md`, `literature-scout.md`, `code-review.md`: summarised from the controller-provided skill summaries in the dispatch; no verbatim copy of long skill text.

- [ ] **Step 1:** Write the files.
- [ ] **Step 2:** Run a one-off check printing the longest memory bullet length across files; must be ≤500.
- [ ] **Step 3:** Commit `docs: Kordi agent files`.
