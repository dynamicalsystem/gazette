---
loop: calendrical-rot-double-post
product: gazette
owner: dynamicalsystem
status: Act
parent: null
blocked-by: []
worktrees: []
prs: []
triggers: []
---

# Calendrical rot double-post regression

## Status

Act

**Owner:** dynamicalsystem

## Context

The `calendrical rot` publishing target is emitting duplicate posts again. A
previous incident was "fixed" by hacking production and burning live content;
that fix did not address the root cause. The current requirement is to
investigate without posting to live channels or advancing production
watermarks. Abyss posts are reported fine.

## Observations

- The tinsnip deployment has two branches with different `gazette-publish.container`
  configs:
  - `main`: `Exec=publish` (dry-run; no `GAZETTE_LIVE=1`).
  - `gazette-publish-live`: `Exec=publish --live` + `Environment=GAZETTE_LIVE=1`.
- The guardrail decision record (`architecture/docs/gazette-prod-guardrails/decision.md`)
  says the Quadlet must pass `--live` and `GAZETTE_LIVE=1`, but the tinsnip `main`
  branch has not been updated to match.
- `gazette-publish.timer` has `Persistent=true` on a daily `OnCalendar` trigger.
  A boot shortly before 07:00 Europe/London can cause a catch-up fire plus the
  scheduled fire.
- `publish_once()` iterates over `watermarks()` keys once per run. It only
  advances a watermark after a successful `publish()`.
- The `Signal` publisher retries on the "incoming messages are regularly received"
  400 path; each retry is a new POST to the Signal service.
- Abyss posts are reported fine; only `calendrical rot` is doubling.

## Orientation

1. **The duplicate is real, not a logging artifact.** On 2026-07-19 the
   scheduled run shows:
   - `06:00:44` Signal `/v2/send` returns `400` for `calendrical_rot` with
     `MismatchedDevicesException: StatusCode: 409`.
   - `06:00:55` gazette retries and gets `201`; the watermark advances from
     `tQ26.H.88` to `tQ26.H.87`.
   - `signal-cli-rest-api` logs confirm two distinct `POST /v2/send` calls for
     `calendrical_rot` in the same run.

2. **Abyss and josh are fine because they do not hit the 409 path.** Only
   `calendrical_rot` triggers `MismatchedDevicesException`, which is a Signal
   group/device-state error, not a gazette scheduling bug.

3. **The retry logic is too broad.** `Signal.publish()` retries on any 400
   except "Unregistered user" and "incoming messages are regularly received".
   The transient-SocketException retry path also catches 409
   `MismatchedDevicesException`. A 409 can mean the Signal server already
   accepted/delivered the message to some devices before rejecting the stale
   device list; retrying therefore sends a second copy.

4. **The previous "fix" addressed symptoms, not the root cause.** Deleting live
   content and resetting watermarks did not change the retry behavior or the
   `calendrical_rot` group state, so the double post regressed as soon as the
   409 reoccurred.

5. **A publish-once idempotency guard would make this class of bug impossible.**
   The `gazette-prod-guardrails` decision record already lists this as a
   deferred guardrail. It belongs in the fix, but the immediate stop-the-bleed
   change is narrower: stop retrying 409s.

## Decision

1. Change `Signal.publish()` to treat `MismatchedDevicesException` (HTTP 400
   with `StatusCode: 409`) as a non-retriable fault. Log it, return `False`,
   and let `publish_once()` hold the watermark and alert the operator. This
   stops the automatic double post on the next run.

2. Add a regression test that asserts a 409 `MismatchedDevicesException` does
   not retry and returns `False`.

3. Implement the deferred **publish-once idempotency guard** so the same
   `(watermark, placing)` pair cannot be published twice within a rolling
   window, regardless of retry logic, manual re-runs, or timer misfires. This
   is the durable fix.

4. Operationally, refresh the `calendrical_rot` Signal group state
   (`signal-cli` device sync / group re-sync) so the held watermark can clear
   on the next scheduled run without another 409.

## Action

- [x] Patch `gazette/src/dynamicalsystem/gazette/publishers.py` to detect and
      reject 409 `MismatchedDevicesException`.
- [x] Add regression test in `pytests/src/dynamicalsystem/pytests/test_signal_client.py`.
- [x] Implement publish-once guard in `gazette/src/dynamicalsystem/gazette/publish_guard.py`
      and wire it into `publish_once()`.
- [x] Add tests for the publish-once guard.
- [x] Validate with dry-run / mocked tests only; no live posts or watermark
      advances.
- [x] Restart `signal-cli-rest-api` on the gateway to refresh Signal state.
- [x] Harden the publish guard: atomic temp-then-rename writes, prune expired
      entries on record, fail open with a loud log on a corrupt guard file.
- [x] Default `data_folder` to `$XDG_DATA_HOME/dynamicalsystem/data` (fallback
      `~/.local/share`) so dev state never lands in the repo cwd. Prod sets
      `DATA_FOLDER` explicitly and is unchanged.
- [x] Commit/push code changes to `main` (8e4ba2b).
- [x] Serialize live sweeps with a non-blocking flock on `publish.lock`
      (f80f5d0): closes the check-then-act race between concurrent sweeps
      (e.g. a manual run alongside the timer) and the read-modify-write race
      in `PublishGuard.record()`. A second live sweep fails fast with a
      non-zero return; dry-runs are unaffected.
- [x] Flip the Signal retry policy to an allowlist (394b5fd): only
      positively identified transient errors retry (RequestException,
      SocketException 400, drain-inbox). Unrecognized errors fail safe --
      return False, hold the watermark, alert -- so a renamed or re-wrapped
      exception can never default back into a duplicate-posting retry.
- [ ] Deploy a new image.
- [ ] Verify the next scheduled run does not double-post `calendrical_rot`.

## Outcomes

### Outcome 1: Root cause of `calendrical rot` double posts is identified

Tests:
- [x] Inspect gateway systemd timers and journal to confirm how many `gazette-publish` services actually started and when.
- [x] Inspect gateway `watermarks.json`, `watermarks.json.log`, and `watermarks.json.bak` to see whether the watermark advanced once or twice per duplicate event.
- [x] Cross-check Signal service logs (`signal-cli-rest-api`) for duplicate `/v2/send` POSTs to the `calendrical rot` target.
- [x] Determine whether the duplicate is a real second post or a logging artifact.

### Outcome 2: Fix is validated without live posts or watermark advances

Tests:
- [ ] Reproduce the suspect path locally or on a non-prod target.
- [ ] Confirm the fix prevents the double post.
- [x] No production watermarks advanced during validation.
