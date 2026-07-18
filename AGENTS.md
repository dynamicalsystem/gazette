# Gazette project instructions

This file extends the user-scope AGENTS.md at `/root/.kimi-code/AGENTS.md`. All
rules there still apply; this file adds project-specific operational guardrails.

## Production publishing

Gazette publishes reviews to real users on Signal and Bluesky. Treating prod as
a test environment burns watermarks, spams users, and makes recovery harder.

When working on gazette:

- **Default to dry-run.** Any `gazette publish` command you suggest or run must
  start without `--live` and without `GAZETTE_LIVE=1`.
- **Require explicit human confirmation before any live post.** If the user asks
  you to publish live, stop and confirm they understand which targets will be
  posted to and which watermarks will advance.
- **Do not iterate on prod.** If a fix needs validation against a real publisher,
  use a non-prod target (Validator dry-run, staging account, or canary
  recipient). Never repeatedly run live commands to debug.
- **Do not change prod watermark state without confirmation.** Advancing or
  resetting a watermark is a production state change. Confirm the current
  placing, chart, and target before acting, and prefer the documented runbook
  in `docs/runbooks/prod-publishing.md`.
- **If in doubt, hold.** A missed post is recoverable; an accidental live post is
  not.
