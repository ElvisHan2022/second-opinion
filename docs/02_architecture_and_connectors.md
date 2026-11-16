# Architecture, Inputs, Outputs and Connectors

Draft for the post-lunch input/output diagram. Edit freely.

## Flow

```
Voice intake  ->  Structured profile  ->  Evidence retrieval  ->  Grading and filtering  ->  Plan generation  ->  Delivery and follow-up
                        ^                                                                                              |
                        |___________________________ wearable and check-in data update the profile ____________________|
```

## Inputs

| Input | Source | Format |
| --- | --- | --- |
| Health background, goals, conditions, medications, supplements | Voice intake | Transcript converted to a JSON profile |
| Risk tolerance and readiness to act | Intake questions | Two ordinal scores (1 to 5) |
| Activity, sleep, resting heart rate, weight trend | Wearables | Daily summaries |
| Self-reported symptoms and adherence | Check-in replies | Short text |

## Outputs

| Output | Content |
| --- | --- |
| Wellness plan | Three to five options, each with pros, cons, evidence level and source links |
| Safety flags | Interactions, contraindications, and prompts to consult a clinician |
| Clinician summary | One-page profile and plan the user can share |
| Nudges | Scheduled reminders and check-in questions |

## Profile schema (minimum)

```json
{
  "user_id": "string",
  "goals": ["string"],
  "conditions": ["string"],
  "medications": [{"name": "string", "approved": true}],
  "supplements_peptides": [{"name": "string", "source": "string"}],
  "risk_tolerance": 3,
  "readiness_to_act": 4,
  "wearable_summary": {"steps_7d": 0, "sleep_hrs_7d": 0, "rhr_7d": 0},
  "updated_at": "ISO-8601"
}
```

## Connectors

| Need | Candidate connector | MVP status |
| --- | --- | --- |
| Voice intake | ElevenLabs voice agent or browser speech API | Demo |
| Clinical evidence | PubMed, ClinicalTrials.gov, FDA labels (openFDA) | Demo |
| Preprints | medRxiv and bioRxiv | Optional |
| Community signal | Reddit (read only, graded as anecdote) | Optional |
| Wearables | Apple Health, Garmin, Whoop APIs | Mocked data |
| Nudges | Email or SMS | Mocked send |
| Collaboration and trace | Kordi | Live |

## Agent roles on Kordi

| Agent | Job |
| --- | --- |
| Intake agent | Runs the voice intake and writes the profile |
| Evidence agent | Retrieves and grades sources for each candidate recommendation |
| Safety agent | Checks interactions and enforces the no-dosing boundary |
| Plan agent | Assembles the plan, tailored to risk tolerance and readiness |

The Kordi thread records each handoff, so every recommendation in the final plan can be traced to the evidence and the agent that produced it.
