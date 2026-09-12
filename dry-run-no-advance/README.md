---
loop: dry-run-no-advance
product: gazette
owner: dynamicalsystem
status: Act
parent: null
blocked-by: []
worktrees: [dry-run-no-advance]
prs: [https://github.com/dynamicalsystem/gazette/pull/8]
triggers: []
---

# Dry-run must not advance watermarks

## Status

Act

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
- [ ] CI green, merge, image built and pulled by the gateway.
- [ ] Dry-run inside the gazette container on the gateway against the live
      data folder; confirm the three watermark files are byte-identical
      before and after.

## Outcomes

### Outcome 1: A dry-run against the live data folder leaves it untouched

Tests:
- [x] Unit test: `publish_once()` (dry-run) with a successful Validator publish
      does not call `watermark.update()` and logs a "would advance" line.
- [x] Unit test: `publish_once(live=True)` still updates the watermark.
- [x] Unit test: a live route whose configured publisher is `Validator`
      advances in live mode.
- [ ] Dry-run of the deployed image on the gateway against the LIVE data
      folder: `watermarks.json`, `.bak` and `.log` are byte-identical before
      and after.

### Outcome 2: Operators can trust the runbook's dry-run instructions

Tests:
- [x] Runbook, README and CLI docstring state that a dry-run does not change
      the data folder, and the runbook's pre-flight steps are correct as
      written.
