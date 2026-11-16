# Evidence Grading and User Classification Rubric

Version 0. Deterministic rules so every grade is reproducible and auditable.

## Source tiers

| Tier | Source type | Default weight | Example |
| --- | --- | --- | --- |
| A | Randomized trials, systematic reviews, clinical guidelines, FDA labels | 1.0 | Phase 3 semaglutide trial, FDA prescribing information |
| B | Observational studies, cohort data, peer-reviewed case series | 0.7 | Registry analysis of GLP-1 discontinuation |
| C | Preprints, expert commentary, professional society statements | 0.4 | medRxiv preprint |
| D | Community reports (Reddit, forums), practitioner opinion | 0.2 | Reddit thread on side effects |
| E | Influencer or commercially interested content | 0.0 for claims; logged as context only | Sponsored TikTok |

## Grading rules

| Rule id | Condition | Result |
| --- | --- | --- |
| R1 | At least one Tier A source supports the claim and none contradicts it | Grade: Strong |
| R2 | Tier B support only, or Tier A with mixed findings | Grade: Moderate |
| R3 | Tier C or D support only | Grade: Limited; shown with a caution label |
| R4 | Only Tier E support | Not presented as a recommendation |
| R5 | Product is a non-FDA-approved peptide | Safety agent adds risk notice and clinician referral; no dosing given |
| R6 | Known interaction with a listed medication | Safety flag overrides grade; shown first |

Every recommendation in the plan stores the rule id that produced its grade.

## User classification

| Axis | Scale | Effect on plan |
| --- | --- | --- |
| Risk tolerance | 1 (very cautious) to 5 (experimental) | Below 3: only Strong and Moderate options shown. 3 or above: Limited options shown with caution labels |
| Readiness to act | 1 (exploring) to 5 (ready now) | Low: education first, fewer options. High: concrete next steps and nudges |

Risk tolerance never unlocks dosing instructions or overrides safety flags.

## Evaluation checks for the demo

1. Same profile, same sources: plan is identical across runs (determinism).
2. A Tier E-only claim never appears as a recommendation.
3. A non-approved peptide always triggers R5.
4. Changing risk tolerance from 2 to 4 changes the option set as specified, and nothing else.
