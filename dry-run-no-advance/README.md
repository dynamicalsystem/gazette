---
loop: dry-run-no-advance
product: gazette
owner: dynamicalsystem
status: Closed
parent: null
blocked-by: []
worktrees: [dry-run-no-advance]
prs: [https://github.com/dynamicalsystem/gazette/pull/8]
triggers: []
---

# [ARCHIVED] Dry-run must not advance watermarks

## Status

Closed

**Owner:** dynamicalsystem

## Context

Found during abyss-lead-invariant on 2026-09-12. The runbook and README both
say `gazette publish` (dry-run) "logs what would be published but does not
post". It does not post, but it does advance every watermark it validates, so a
dry-run against the gateway's data folder would move prod forward without any
content being delivered. Simon asked for this to be fixed in its own loop.

## Observations

- `Validator.publish()` logs the formatted post and returns True.
- `_sweep` in `gazette/__init__.py` calls `publisher.watermark.update()` on any
  True return, in both modes. Only the publish-once guard record is gated on
  `live`.
- `Watermark.update()` decrements the placing, rewrites `watermarks.json`,
  writes `.bak` and appends to `.log`. A dry-run therefore leaves the same
  footprint as a live run except for the guard file and the post itself.
- Demonstrated 2026-09-12 15:42 UTC on the gateway against a copy of the data
  folder: the copy's log gained three `old=... new=...` lines.
- The runbook's "Advancing or resetting a watermark" section tells the operator
  to "verify with `gazette publish` (dry-run)" after a manual change, and the
  "When is live prod access permitted?" section requires a dry-run first. Both
  would decrement prod watermarks if run inside the gazette container.
- `watermarks.example.json` has a route whose configured publisher is
  `Validator` (target `dev`). In LIVE mode that route is a real route and must
  advance. The problem is the mode, not the publisher class.
- Tests: `test_publish_once_records_live_publish_and_skips_duplicates` asserts
  the watermark updates on a live run. No test asserts what a dry-run does to
  the watermark.

## Orientation

The guard is already gated on `live`; the watermark update is not. A dry-run
that advances is a dry-run that can only be run once per day, and only against
a copy, which defeats its purpose as a pre-flight check.

The fix belongs in `_sweep`, not `Validator`: a route configured with the
Validator publisher is a legitimate live route (dev/validation) and must
advance when run live. Gate `watermark.update()` on `live`, exactly as the
guard record already is, and log "would advance" in dry-run.

With the follows rule now in place, a dry-run that does not advance reproduces
the next live sweep exactly: start placings are captured, followers hold or go
by the same comparison, and nothing moves.

## Decision

Gate the watermark update on `live` in `_sweep`. Dry-run logs what it would
have advanced. Align the CLI docstring, README and runbook to say the dry-run
touches nothing in the data folder. No change to `Validator`.

## Action

- [x] Branch `dry-run-no-advance`: watermark update gated on `live` in
      `_sweep`; dry-run logs `would advance`; CLI docstring, README and
      runbook aligned; four tests in test_dry_run.py; existing
      advancement tests switched to live sweeps with the lock patched.
- [x] PR #8 opened.
- [x] CI green; merged as dd3c353 2026-09-12; release run 34703865915; gateway
      auto-update pulled image 9ae3d0e8f8b7 at 16:02 UTC.
- [x] 16:04 UTC: dry-run of the new image on the gateway, first against a
      copy (unchanged), then against the live data folder. sha256 of
      watermarks.json, .bak and .log identical before and after. Log shows
      `would advance` for abyss/bluesky/calendrical_rot and josh held.

## Outcomes

### Outcome 1: A dry-run against the live data folder leaves it untouched

Tests:
- [x] Unit test: `publish_once()` (dry-run) with a successful Validator publish
      does not call `watermark.update()` and logs a "would advance" line.
- [x] Unit test: `publish_once(live=True)` still updates the watermark.
- [x] Unit test: a live route whose configured publisher is `Validator`
      advances in live mode.
- [x] Dry-run of the deployed image on the gateway against the LIVE data
      folder: `watermarks.json`, `.bak` and `.log` are byte-identical before
      and after (2026-09-12 16:04 UTC).

### Outcome 2: Operators can trust the runbook's dry-run instructions

Tests:
- [x] Runbook, README and CLI docstring state that a dry-run does not change
      the data folder, and the runbook's pre-flight steps are correct as
      written.
