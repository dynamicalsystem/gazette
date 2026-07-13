---
loop: prod-path-firing-investigation
product: gazette
owner: dynamicalsystem
status: Act
parent: null
blocked-by: []
worktrees: []
prs: []
triggers: []
---

# Production path firing investigation

## Status

Act

**Owner:** dynamicalsystem

## Context

Production delivery paths are showing inconsistent firing behaviour. The Signal
path produced duplicate output this morning, while the Bluesky path has stopped
firing entirely. This loop exists to determine whether the failures share a root
cause or are independent incidents, and to restore reliable delivery on both
paths.

## Observations

- Signal path appeared to fire twice on the morning of 2026-07-13.
- Bluesky path has not fired since 2026-07-10 06:37 UTC.
- Production runs as tinsnip quadlets on the `gateway` box (loop 07). The publish
  sweep is a one-shot container driven by `gazette-publish.timer` at 07:00
  Europe/London; logs are emitted to stdout and captured by systemd journald.
- Watermark state lives on the box at
  `~/.local/state/dynamicalsystem/gazette/watermarks.json`.
- Gateway access is available via `ssh -i ~/.ssh/id_oci ubuntu@152.67.153.4`.
- `journalctl -u gazette-publish` is empty; application logs are found in the
  system journal under the `gazette-publish` syslog identifier.
- Every scheduled run since 2026-07-08 shows two parallel PIDs logging identical
  messages at identical timestamps (e.g. 1631014 and 1631050 on 2026-07-08).
- Watermarks advance exactly one placing per target per day, even though log
  lines are duplicated.
- `signal-cli-rest-api` received only one POST `/v2/send` per target per run.
- Bluesky failure started on 2026-07-11 with:
  `ERROR - Unexpected error on watermark bluesky -- FAULT, held.`
- The full exception on 2026-07-13 is:
  `AttributeError: 'Bluesky' object has no attribute 'message'`.
- The deployed image on the box is `ghcr.io/dynamicalsystem/gazette:latest`
  (revision `ecd2992f...`, built 2026-07-10T07:15:17Z).
- The bug is in `gazette/src/dynamicalsystem/gazette/publishers.py` line 69:
  `self.logger.error(f"Message too long: {size} {self.message}")` references
  `self.message`, which does not exist on the `Bluesky` class.
- The watermark for `bluesky` was tQ26.H.97 while the Bluesky path was stuck.
- Bluesky's app-level post limit is 300 Unicode extended grapheme clusters, not
  raw characters or bytes. The atproto wire limit is 3000 chars.
- A manual run on 2026-07-13 published a truncated tQ26.H.97 Bluesky post. That
  post has been deleted, and the `bluesky` watermark has been reset to 96 so the
  next scheduled run publishes tQ26.H.96 cleanly.

## Orientation

1. **Signal "duplicate": not a real duplicate.** The two PIDs are the podman
   process (1631014) and the container's main process (1631050). Both write the
   same stdout lines to journald because podman's default log driver is
   `journald` and systemd also captures the service's stdout. The service starts
   exactly once per timer trigger, watermarks advance once per target per day,
   and `signal-cli-rest-api` logs show exactly one `/v2/send` per target per run.
   The perceived duplicate is a logging artifact, not duplicate delivery.
2. **Bluesky silence: code regression in the 2026-07-10 image.** When a Bluesky
   message exceeded 300 chars, the publisher tried to log `self.message` and
   raised `AttributeError`. `publish_once()` caught this as an unexpected fault,
   held the watermark, and the same placing was retried every day with the same
   failure. The tQ26.H.97 review is long enough to hit the limit, so Bluesky has
   been stuck since the new image was pulled.
3. **Truncation is the wrong fix.** Bluesky's limit is 300 Unicode extended
   grapheme clusters, not Python `len()`. Silently truncating a review rewrites
   the content and bypasses the existing `ReviewInvalid` quality gate. The
   correct behaviour is to reject the long review during publisher construction
   so it is held back rather than mangled and published.

The Signal and Bluesky symptoms are independent. No shared root cause.

## Decision

1. Fix the Bluesky publisher bug: replace `self.message` with a valid log line.
2. Enforce Bluesky's 300-grapheme limit by raising `ReviewInvalid` in the
   `Bluesky` publisher constructor. Do not truncate; hold the review back so it
   can be rewritten or split.
3. Build and push a new `ghcr.io/dynamicalsystem/gazette:latest` image.
4. Let the gateway's `podman auto-update` pull the fixed image. Do not run a
   manual production publish sweep; wait for the scheduled 07:00 Europe/London
   timer.
5. Do **not** change the Signal path: it is already firing once per event; the
   duplicate logs are a harmless journald duplication. We can optionally clean
   up the double-logging later, but it is not blocking delivery.

## Action

- [x] Access gateway box logs and watermarks.
- [x] Identify the last successful Bluesky firing and failure signals.
- [x] Identify the exact Signal duplicate event and compare with normal firings.
- [x] Confirm root causes for both paths.
- [x] Fix `self.message` bug in `gazette/src/dynamicalsystem/gazette/publishers.py`.
- [x] Replace Bluesky truncation with a 300-grapheme `ReviewInvalid` check.
- [x] Add `grapheme>=0.6.0` dependency and update regression test.
- [x] Commit and push the fixes to `main` (commit `f0984ab`).
- [x] Build and push the multi-arch image to GHCR.
- [x] Trigger `podman-auto-update.service` on the gateway to pull the fixed image.
- [x] Delete the truncated Bluesky post and reset the `bluesky` watermark to 96.
- [ ] Observe the next scheduled runs to confirm both paths are healthy.

### Verification (2026-07-13 17:42 UTC)

- CI `release.yml` run `29271264751` built and pushed
  `ghcr.io/dynamicalsystem/gazette:latest` successfully.
- Gateway `podman-auto-update.service` pulled the new image and notified Abyss
  (HTTP 201).
- The truncated tQ26.H.97 Bluesky post was deleted and the `bluesky` watermark
  reset to 96.
- No manual production publish sweep was run after the reset. The next Bluesky
  publish will be tQ26.H.96 at the scheduled 07:00 Europe/London run.

## Outcomes

### Outcome 1: Signal path fires exactly once per intended event

Tests:
- [x] Root cause of duplicate Signal firing is identified (logging artifact).
- [x] Verified in production: only one POST `/v2/send` per target per run and
      watermarks advance exactly one placing per day.
- [ ] No duplicate Signal firings observed for 48 hours after the finding
      (continue to monitor).

### Outcome 2: Bluesky path resumes reliable firing

Tests:
- [x] Root cause of Bluesky silence is identified (`AttributeError` on long
      message log line, then message length rejection).
- [x] Fix is applied and image is deployed on the gateway.
- [x] Long Bluesky posts raise `ReviewInvalid` instead of being truncated.
- [ ] Bluesky path publishes tQ26.H.96 cleanly at the next scheduled run.
- [ ] Bluesky path continues to fire normally for 48 hours after recovery.
