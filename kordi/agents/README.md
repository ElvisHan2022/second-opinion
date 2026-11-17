# Kordi agent files

One markdown file per agent. Attach the file to `credence-build`, then import its Memory bullets into the owner's Kordi agent. Each person has their own agent plus the shared Facilitator; an agent's role comes from its imported memory bullets, attached documents and the `@` folder reference, and it acts when mentioned.

| Agent | File | Owner (suggested) | Trigger |
| --- | --- | --- | --- |
| Intake Agent | [`intake.md`](intake.md) | Elvis | `@Intake Agent` |
| Clinical Evidence Agent | [`evidence-clinical.md`](evidence-clinical.md) | Partner | `@Clinical Evidence Agent` |
| Public Opinion Agent | [`public-opinion.md`](public-opinion.md) | Partner | `@Public Opinion Agent` |
| Response Composer | [`response-composer.md`](response-composer.md) | Elvis | `@Response Composer` |
| Plan Agent | [`plan.md`](plan.md) | Elvis | `@Plan Agent` |
| Safety Agent | [`safety.md`](safety.md) | Beth Porter (build support) | `@Safety Agent` |
| Persona Twin | [`persona-twin.md`](persona-twin.md) | Partner | `@Persona Twin` |
| Evidence Auditor | [`evidence-auditor.md`](evidence-auditor.md) | Beth Porter (build support) | `@Evidence Auditor` |
| Referee | [`referee.md`](referee.md) | Beth Porter (build support) | `@Referee` |
| Shah Audit | [`shah-audit.md`](shah-audit.md) | Beth Porter (build support) | `@Shah Audit` |
| Literature Scout | [`literature-scout.md`](literature-scout.md) | Beth Porter (build support) | `@Literature Scout` |
| Code Review Agent | [`code-review.md`](code-review.md) | Elvis | `@Code Review Agent` |

Owners are suggestions. Any teammate can mention any agent.

## How to use an agent in Kordi

1. Attach the agent's file to `credence-build` (and the documents it lists under Attach).
2. Import the file's Memory bullets into the owner's agent (web app: import the `.md` file; each extracted memory is capped at 500 characters, and every bullet here is under that).
3. In the owner's agent chat, `@`-reference the repo folder once so the agent works in it.
4. Mention the agent with the message in its Trigger block. Plain messages are context and do not start a run.

## Tags

From `docs/KORDI_WORKFLOW.md` section 3. The trace export is parsed by these tags.

| Tag | Use |
| --- | --- |
| `[DECISION]` | A choice the team made and why |
| `[BUG]` | Kordi bug or friction: what you did, what happened, what you expected |
| `[RESPONSE r-###]` | A plan posted for rating |
| `[RATING r-###]` | A rating reply |
| `[MILESTONE M#]` | A milestone completed, with a commit link |

## Rules every agent follows

- Synthetic personas only (demo persona p-002).
- Memories hold task rules only; health content stays in attached files (`docs/KORDI_WORKFLOW.md` section 6).
- Never output dosing, administration or sourcing instructions for non-FDA-approved peptides.
