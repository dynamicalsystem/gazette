# Gazette production publishing guardrails

**Status:** Implemented and deployed (PR #6).

**Decision date:** 2026-07-15 UTC.

## Problem

On 2026-07-13, a live publishing incident burned down multiple gazette reviews in a single day. The response pattern was unsafe: prod was used as the test environment, watermarks were advanced manually, and fixes were validated by posting live content to real users.

## Guardrails in place

1. **Dry-run by default.** `gazette publish` runs every watermark through the `Validator` publisher unless `--live` is passed.

2. **Explicit live opt-in.** Real publishers require both:
   - `gazette publish --live`
   - `GAZETTE_LIVE=1` in the environment

   Missing either one exits with an error and no target is touched.

3. **Watermark audit trail.** Every `Watermark.update()` snapshots `watermarks.json` to `watermarks.json.bak` before writing, and appends a line to `watermarks.log` with the old and new placing.

4. **Operational runbook.** See `docs/runbooks/prod-publishing.md` in the gazette repo for the full procedure.

5. **AI instructions.** Project `AGENTS.md` requires human confirmation before any live post or prod watermark change.

## Quadlet configuration

The tinsnip `gazette-publish` Quadlet unit must pass `--live` and set `GAZETTE_LIVE=1`:

```ini
[Container]
Exec=gazette publish --live
Environment=GAZETTE_LIVE=1
```

Do not put `GAZETTE_LIVE=1` in the shared `EnvironmentFile=`; keep it scoped to the publish unit so `gazette serve` and manual shells stay dry-run by default.

## Deferred guardrails

The following were considered but not implemented in the first cut:

- **Publish-once guard:** track `(watermark, placing)` pairs already published to refuse repeats.
- **Per-target rate limit:** reject a publish if the target already fired within N hours.
- **Canary/staging targets:** non-prod Signal group or Bluesky account for integration testing.

Add these if the scheduled daily run shows it is vulnerable to double-firing or if publisher integration testing becomes routine.
