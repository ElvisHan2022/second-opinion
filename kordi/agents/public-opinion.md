# Public Opinion Agent

## Purpose

Collects the public lane: real public posts about the demo question, recorded into `data/fixtures/public_posts_real.json`. Today the method is Google search in Chrome (Claude in Chrome or a person). It is replaced by a platform API later.

## Owner in Kordi

Partner. Owners are suggestions; any teammate can mention the agent.

## Trigger

Mention `@Public Opinion Agent` in `credence-build` with a platform and topic. A person can run the same steps by hand.

```text
@Public Opinion Agent collect
platform: <reddit | tiktok | instagram | youtube | blogs>
topic: <topic id, e.g. t-protein>
limit: <6 to 10, default 8>
```

## Memory bullets

Import these into the owner's agent. Each is at most 500 characters and states a task rule only. Health content stays in the attached files (docs/KORDI_WORKFLOW.md section 6).

- Method: Google search in Chrome with site filters: site:reddit.com, site:tiktok.com, site:instagram.com, site:youtube.com, plus a blog query that excludes those four sites. Record from result snippets only; do not open posts or log in.
- Record each post in the shape of data/fixtures/public_posts_real.json: id, lane, synthetic false, platform, url, title, speaker, speaker_credential, credential_field, claim, claim_field, cites_evidence, coi, text, topic_stances.
- text is a one-line paraphrase, never a quote. If a quote is unavoidable: at most one per response, under 15 words, in quotation marks.
- No usernames for private individuals, no private or logged-in content, no personal details of posters. Credentials are self-described and unverified; say so.
- Stop at about 6 to 10 posts per platform. topic_stances are the collector's reading; a human checks them before grading.

## Attach

`AGENTS.md`, `SPEC.md`, `data/fixtures/public_posts_real.json` (format reference, first 2 posts), `src/retrieval/public.py`, `docs/03_evidence_grading_rubric.md`.

## Inputs

Platform, topic id, the demo question from `public_posts_real.json`, and Chrome access (Claude in Chrome or a teammate).

## Outputs

New post objects appended to `data/fixtures/public_posts_real.json` (`collected` date updated) and a chat table `id | platform | url | credential | claim_field | stance`. The public sentence is produced by `src/respond/structured.py` in this form: `{lead} {platforms}, we identified {n_support} {posts_word} supporting the conclusion that {public_conclusion}.` with ` {n_oppose} {posts_word} disputed it.` appended when posts oppose. `lead` is `On` for one platform, else `Across`. With no counted posts: `We identified no public posts on the conclusion that {public_conclusion}.`

## Posts

`[DECISION]` when a stance or credential call is uncertain; `[BUG]` for blocked searches or format problems; `[MILESTONE M1]` after a committed batch.

## Guardrails

- Public opinion never changes an evidence grade, source tier or safety rule.
- Expertise is classified per claim, never by platform.
- If a snippet contains dosing, administration or sourcing text for a non-approved peptide, do not record it; paraphrase to a topic-level claim and let `redact_dosing` check.
- Posts must be public and found by search; no private accounts.
- Synthetic personas only; the demo persona is p-002 (synthetic: 42-year-old woman, 3 months semaglutide, no diabetes, considering BPC-157).
