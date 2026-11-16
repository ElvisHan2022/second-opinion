# Design: NEJM/Lancet sources, evidence ring frontend, Kordi agents doc

Date: 2026-11-16. Status: approved by Elvis; OpenEvidence swapped for NEJM/Lancet at 15:50.

## Why

The demo has to show, at a glance, where medicine and the public agree or split on one question. NEJM and Lancet are names clinicians and the public both recognise, so badging them makes the medical side legible. The boxing ring makes the medicine-versus-public gap concrete. The Kordi agents doc lets teammates and judges run the same roles in Kordi, so the trace shows the collaboration.

## Decisions (made by Elvis)

| Question | Choice |
| --- | --- |
| Clinical sources | PubMed, with NEJM and Lancet papers via PubMed journal filters (no OpenEvidence access) |
| Ring corners | By per-claim classification. Platform logo is only a badge |
| Frontend stack | Static HTML/JS page fed by a JSON export, instead of Streamlit |
| Agents in the Kordi doc | Pipeline roles and selected Claude Code skills |

## Approaches considered

- **Clinical sources:** NEJM/Lancet through PubMed (chosen: legal, cached, abstracts available); OpenEvidence paste-in or API (dropped: no access); scraping journal sites (rejected by SPEC).
- **Ring corners:** by classification (chosen: follows AGENTS.md "never by platform"); by platform (rejected: misplaces the pharmacist on X and the physicians on YouTube).
- **Frontend:** static page (chosen: full design control, works offline from `file://`); Streamlit with an HTML component (keeps SPEC's stack but limits the look).

## 1. NEJM and Lancet through PubMed (replaces OpenEvidence)

Update 15:50: Elvis has no OpenEvidence access. Clinical sources for now are PubMed, NEJM and Lancet.

- NEJM and Lancet papers are indexed in PubMed, so `clinical.py` gets one more query: the demo topics restricted to `"N Engl J Med"[ta] OR "Lancet"[ta] OR "Lancet Diabetes Endocrinol"[ta]`. It returns titles, abstracts and publication types through the same cached E-utilities client. This is not scraping, and no full text is fetched.
- Each clinical `Source` gets a `journal` field (the full PubMed journal title, plus its abbreviation `ta`). The UI badges the source as NEJM, Lancet or PubMed from that field.
- OpenEvidence stays listed as a future source in SPEC. No code for it today.

## 2. Expert classifier (pulled forward from M2)

The ring needs each source's category. `src/classify/expert.py` implements the SPEC section 4 table exactly, plus a credential coverage map: each credential field lists the claim fields it covers (for example internal medicine covers obesity medicine). That fixes the pub-02 internist case. The out-of-field flag is set when the credential does not cover the claim field. Clinical-lane sources are expert_evidence. Tiers and grades (R1 to R6) stay in M2.

## 3. Frontend: `app/index.html`

- `src/export_demo.py` writes `app/demo_data.js` (`window.DEMO = {...}`) from the persona and the classified sources, so the page opens straight from disk.
- **Layout (OpenEvidence-style, not its branding):** a quiet header with the product name, a large question box holding the demo question, and an answer card with inline numbered citations. A references list shows grade and category badges. Below that is a "Medicine vs Public" section containing the ring.

```
 Second Opinion                                    synthetic demo, not medical advice
 ┌──────────────────────────────────────────────────────────────────┐
 │ How do I avoid losing muscle on semaglutide ... BPC-157?        │
 └──────────────────────────────────────────────────────────────────┘
 Answer  (plan after M3; until then: evidence summary per topic) [1][2]
 References  [1] SURMOUNT-1 body comp ... RCT · expert_evidence · Lancet/NEJM/PubMed badge

 ┌──────────────────────── THE RING ────────────────────────┐
 │ MEDICINE corner              vs            PUBLIC corner │
 │ [PubMed] [NEJM] [PharmD·X]        [Reddit] [TikTok·infl]│
 │ [MD·YouTube] [RD·IG]              [Coach·IG] [DC·TikTok*]│
 │ Scorecard: where they agree / where they split           │
 └──────────────────────────────────────────────────────────┘
```

- Each fighter is a card: speaker type, credential, a platform badge, a category chip, and a COI marker. Out-of-field speakers sit in the public corner with an "out of field" tag.
- Clicking a fighter shows its claim and source.
- The scorecard lists claims both corners make (agree) and claims where they differ (split). Its first version is hand-tagged claim topics in the fixtures; M3 replaces it with the plan's `medical_vs_public`.
- Icons are simple inline SVG or letter glyphs with platform names, not copied brand logos. No OpenEvidence, NEJM or Lancet logos; journal badges are text.
- Institutional fighters (Stanford, hospitals) appear only if real sources from them are added. None are invented.
- Light and dark mode, readable on a projector, and it works with no network.

## 4. Kordi agents doc: `docs/07_kordi_agents.md`

One card per agent: purpose; who owns it in Kordi (whose personal agent, or the Facilitator); trigger (an @mention plus a message format); memory bullets of 500 characters or fewer, ready to import; documents to attach; workspace reference; inputs and outputs; and the tags it posts.

- **Pipeline roles:** Intake, Evidence, Safety, Plan, Persona twin, Evidence auditor. Judge roles are told to run on a different model family at temperature 0.
- **Claude Code skills recast as Kordi agents:** referee (adversarial review), shah-audit (deployment audit of clinical AI), scout (literature landscape), code-review (bugs before commit).

## Non-goals

No OpenEvidence code, no scraping of NEJM, Lancet or other journal sites. No grading or plan generation (M2 and M3). No Streamlit page. No real people's posts or health information.

## Anti-goals

A ring that sorts sources by platform. Fighters that represent sources we do not have. Any peptide dosing on screen.

## Left to the builder

Visual style details, animation, file layout inside `app/`, and the exact coverage map entries. Each is noted as the builder's call.

## Update 15:55 (Elvis)

- **Kordi agents** become one markdown file per agent under `kordi/agents/`, ready to attach in the Kordi channel. That replaces the single `docs/07_kordi_agents.md`.
- **New Response composer agent.** It fills two fixed templates for each claim topic:
  - Clinical: "From {sources} sources (most reputable), we identified {n} studies with study sizes of {sizes}, with the main finding that {finding}. Thus, we recommend {recommendation}."
  - Public, the "court of public opinion": "Across {platforms}, we identified {n} posts supporting the conclusion that {conclusion}."
  - Study sizes are extracted from PubMed abstracts. Finding and recommendation are hand-written per topic today; an LLM generator can replace them in M3.
  - Recommendations never contain peptide dosing.
- **New Public opinion agent.** It collects real posts by Google search in Chrome, using site filters for TikTok, Instagram, Reddit and blogs. It writes them to the `public_posts.json` shape, and an API replaces the search later.
- **Demo page answer card** shows the two sentences per topic, labelled "Medical evidence" and "Court of public opinion".
