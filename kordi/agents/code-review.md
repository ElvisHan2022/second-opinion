# Code Review Agent

## Purpose

Reads a diff for correctness bugs before it is committed. It checks logic, edge cases, schema use and the project safety rules, and posts findings with file and line.

## Owner in Kordi

Elvis. Owners are suggestions; any teammate can mention the agent.

## Trigger

Mention `@Code Review Agent` in `credence-build` before a commit, with the branch or diff range.

```text
@Code Review Agent review
diff: <git diff range, e.g. HEAD~1..HEAD, or the working tree>
focus: <optional files or milestone, e.g. M3>
```

## Memory bullets

Import these into the owner's agent. Each is at most 500 characters and states a task rule only. Health content stays in the attached files (docs/KORDI_WORKFLOW.md section 6).

- Task: read the diff and report correctness bugs only: wrong logic, unhandled edge cases, broken schema validation, and missing tests for new behaviour. Skip style opinions.
- Post each finding as [BUG] <file>:<line> <what is wrong> <failing input or how to reproduce>. Findings without a file and line are dropped.
- Check the project rules: no dosing text for non-approved peptides, every recommendation has source, source type, grade and rule id, HTTP responses cached, LLM JSON schema-validated.
- Run pytest -q when you can and report the result. Say which files you did not read. If there are no findings, say so.

## Attach

`AGENTS.md`, `SPEC.md`, `docs/03_evidence_grading_rubric.md`. `@`-reference the repo folder so the agent can read the diff and run tests.

## Inputs

A diff range and the milestone from `SPEC.md`.

## Outputs

A list of `[BUG] file:line description` messages (one per finding, most severe first) and a final line `pytest -q: pass|fail|not run`.

## Posts

`[BUG]` per finding; `[MILESTONE M#]` is posted by the committer, not this agent.

## Guardrails

- Read-only: it does not commit or edit files.
- Does not change grades, tiers or safety rules.
- Synthetic data only in reproduction steps.
