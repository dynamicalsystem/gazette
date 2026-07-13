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
- The current watermark for `bluesky` is tQ26.H.97; the message at that placing
  exceeds the 300-char limit and triggers the buggy log line every run.

## Orientation

1. **Signal "duplicate": not a real duplicate.** The two PIDs are the podman
   process (1631014) and the container's main process (1631050). Both write the
   same stdout lines to journald because podman's default log driver is
   `journald` and systemd also captures the service's stdout. The service starts
   exactly once per timer trigger, watermarks advance once per target per day,
   and `signal-cli-rest-api` logs show exactly one `/v2/send` per target per run.
   The perceived duplicate is a logging artifact, not duplicate delivery.
2. **Bluesky silence: code regression in the 2026-07-10 image.** When a Bluesky
   message exceeds 300 chars, the publisher tries to log `self.message` and
   raises `AttributeError`. `publish_once()` catches this as an unexpected fault,
   holds the watermark, and the same placing is retried every day with the same
   failure. The tQ26.H.97 review is long enough to hit the limit, so Bluesky has
   been stuck since the new image was pulled.

The two symptoms are independent. No shared root cause.

## Decision

1. Fix the Bluesky publisher bug: replace `self.message` with a valid log line.
2. Truncate Bluesky posts to 300 chars (Bluesky's limit) instead of returning
   `False`, so a long review does not block the path indefinitely.
3. Build and push a new `ghcr.io/dynamicalsystem/gazette:latest` image.
4. Let the gateway's `podman auto-update` pull the fixed image for the next
   scheduled run (or trigger it manually for faster recovery).
5. Do **not** change the Signal path: it is already firing once per event; the
   duplicate logs are a harmless journald duplication. We can optionally clean
   up the double-logging later, but it is not blocking delivery.

## Action

- [x] Access gateway box logs and watermarks.
- [x] Identify the last successful Bluesky firing and failure signals.
- [x] Identify the exact Signal duplicate event and compare with normal firings.
- [x] Confirm root causes for both paths.
- [x] Fix `self.message` bug in `gazette/src/dynamicalsystem/gazette/publishers.py`.
- [x] Add regression test for Bluesky long-message path.
- [x] Commit and push the fixes to `main` (commits `ca35e89`, `96477b2`).
- [x] Build and push the multi-arch image to GHCR.
- [x] Verify the gateway pulls the new image and the next publish run succeeds
      for Bluesky.
- [ ] Observe the next 48 hours to confirm both paths are healthy.

### Verification (2026-07-13 10:23 UTC)

- Manually triggered `gazette-publish.service` on `gateway` after auto-update.
- Bluesky: published `tQ26.H.97` (truncated from 338 to 300 chars) and watermark
  advanced from 97 to 96.
- Signal: published `tQ26.H.93` for `calendrical_rot` and `josh` (one retry on
  transient `SocketException`); watermarks advanced from 93 to 92.
- Watermark file now shows `bluesky` at 96 and all Signal targets at 92.
- No faults held; run completed cleanly.

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
- [x] Fix is applied and verified in production.
- [x] Bluesky path fires successfully at least once after the fix.
- [ ] Bluesky path continues to fire normally for 48 hours after recovery.
