# How we use Kordi

Kordi is the team's collaboration layer and the record of trust ratings. This process follows Kordi's own documentation in the open-source repo (github.com/Kordi-AI/Kordi, `docs/`).

## 1. Setup (once, about 15 minutes)

1. **App.** Use the Mac app if possible, since local agents run on the Mac with your tools; the web app at kordi.ai works for chat, documents and ratings.
2. **Memory import.** On the Mac, import `AGENTS.md` and `CLAUDE.md` into memory. In the web app, import them as `.md` files (up to 20 files, 200 KB each). Each extracted memory is capped at 500 characters, which is why AGENTS.md bullets are short.
3. **Connectors.** Connect GitHub only. Leave Gmail, Calendar and Slack off for the hackathon.
4. **Groups.** Create two group chats:
   - `credence-build`: Elvis, partner, Beth Porter, and each person's agent. Decisions, bugs and build coordination.
   - `credence-ratings`: the team plus stakeholder raters (physicians, nurses, dietitians, engineers, public users). Plans are posted here and rated.
5. **Documents.** Attach to `credence-build`: `SPEC.md`, `AGENTS.md`, `docs/01_project_brief.md`, `docs/03_evidence_grading_rubric.md`, `docs/06_trust_evaluation_loop.md`, this file. Attach only `docs/01_project_brief.md` and the rating instructions (section 4) to `credence-ratings`.
6. **Local agent workspace.** In a Mac agent chat, reference the repo folder once, for example `@~/hackathon/wellness-coach`, to select it as the working directory. The selection persists for that session.

## 2. Keep context retrievable

- A group agent sees only the last eight messages (about 800 characters each) at the start of a turn and retrieves older history with search tools. Keep messages short and put durable context in attached documents or AGENTS.md.
- Mention an agent explicitly to start work. Plain messages are context and do not trigger a run.
- Long tasks spawn a background session linked from the chat; open it in the companion pane to follow progress.

## 3. Message tags

Every tagged message is machine-readable in the trace export.

| Tag | Use |
| --- | --- |
| `[DECISION]` | A choice the team made and why |
| `[BUG]` | Kordi bug or friction: what you did, what happened, what you expected |
| `[RESPONSE r-###]` | A plan posted for rating |
| `[RATING r-###]` | A rating reply |
| `[MILESTONE M#]` | A milestone completed, with a commit link |

## 4. Rating instructions (paste into `credence-ratings`)

> Each plan ends with an id like `[RESPONSE r-001]`. Reply to it with:
> `[RATING r-001] role=<physician|nurse|dietitian|engineer|public> format=<thumbs|stars5|ten|hundred|text> score=<your score> act=<yes|not_yet|no>`
> then any comments. Choose whichever scoring format feels natural; the choice itself is part of what we study. Clinicians: please flag any safety problem with `SAFETY:` at the start of your comment.

## 5. Export traces

Right-click a chat in the sidebar and choose **Export**. Kordi writes `kordi-trace-<title>-<YYYYMMDD-HHmm>.jsonl` (schema `kordi.session-trace`, version 1): one session line, then every message in order with sender, role, text, reply link and, for your own agent, its tool calls. Save exports to `data/fixtures/kordi_traces/` and run `src/eval/kordi_trace.py`.

Export only includes what your own view can show; other members' agent reasoning is excluded and secrets are redacted.

## 6. Privacy and a known constraint

- Synthetic personas only. Never post real health details.
- Kordi's "Keep sensitive details out of memories" setting rejects memories matching health keywords, and digest runs refuse health-category memories. Expect health-related memories from this project to be blocked. Keep memories about the task, keep health content in attached documents, and log any surprising block as a `[BUG]` or finding.

## 7. End of day

1. Export both groups' traces.
2. Copy all `[BUG]` messages into `docs/05_kordi_bug_log.md` and the submission form.
3. Commit traces (synthetic content only) and the final bug log.
