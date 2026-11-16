# Project Brief: Voice Wellness Coach for GLP-1 and Peptide Users

AI in Science Collaboration Hackathon, Stanford, Nov 16, 2026. Team: Elvis Han and partner.

## Problem

Wellness information is fragmented and incentive-misaligned. Naturopaths, influencers, TikTok and Reddit give conflicting advice, often from sources that profit from what they recommend. People who can pay hire personal coaches or nutritionists; most cannot, and are left to sort the evidence alone.

The gap is widest for GLP-1 and peptide users. GLP-1 use is now common, and physicians increasingly report patients disclosing use of peptides that are not FDA-approved. These users make consequential decisions with limited, low-quality guidance.

## Proposed solution

A voice agent that:

1. Conducts a spoken intake covering health background, goals, current medications and supplements, and conditions. Speaking tends to elicit fuller disclosure than typing forms.
2. Produces a personalized wellness plan that presents options with pros, cons and an explicit evidence level for each, and avoids hard prescriptions.
3. Tracks physical and mental health over time through wearable integrations (Apple Watch, Garmin, Whoop).
4. Follows up through text or email nudges, such as daily reminders and check-ins.

## Design principles

- **Loyal to the user.** The agent has no affiliate, supplement or product incentive, and it discloses the provenance of every recommendation. This answers the incentive misalignment that defines the problem.
- **Evidence-graded.** Every claim carries a source and an evidence level. Clinical trials and guidelines outrank forum anecdotes and influencer content (see `03_evidence_grading_rubric.md`).
- **Risk-aware.** Users are classified by willingness to act and by risk tolerance, and the plan adapts to both.
- **Safety boundary.** The agent does not provide dosing or administration instructions for non-approved peptides. It explains known risks, flags dangerous interactions, and routes users to a clinician or pharmacist.

## Differentiation from a general chatbot with connectors

| General chatbot | This product |
| --- | --- |
| Answers each question in isolation | Keeps a longitudinal record of intake, plan and wearable trends |
| Source mix opaque | Transparent evidence grade per recommendation |
| User must initiate | Proactive nudges and check-ins |
| Generic risk framing | Plan conditioned on the user's risk tolerance and readiness to act |
| No clinician handoff | Structured summary a user can bring to a clinician |

## MVP scope (today)

- Population: GLP-1 and peptide users
- Demo: one voice intake, one evidence-graded plan, one follow-up nudge, and the scoring logic shown on screen
- Out of scope: real wearable data ingestion, payments, clinical deployment

## Business model options

- Freemium for individuals
- Employer-paid, positioned as benefits navigation for employees on GLP-1 therapy

## Open questions for collaborators

- How should source weights vary by user (for example, a cautious user versus an early adopter)?
- What evidence would a clinician need to trust the plan summary?
- Which wearable signals are most informative for GLP-1 users (weight trend, resting heart rate, sleep, activity)?
