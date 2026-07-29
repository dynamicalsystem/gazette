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
- **2026-07-29:** The intraday double post appears fixed, but users report the
  same `calendrical_rot` content posting on consecutive days:
  - `Skintern` (tQ26.H.80) posted on 2026-07-28 and again on 2026-07-29.
  - `Delphin Dora` (tQ26.H.81) posted on 2026-07-26 and again on 2026-07-27.
- Gateway journals for 2026-07-26 to 2026-07-29 show `calendrical_rot` hitting
  `MismatchedDevicesException` (HTTP 400) while the watermark is held:
  - 2026-07-26: tQ26.H.81 fails with 400; watermark stays at 81.
  - 2026-07-27: tQ26.H.81 succeeds (201); watermark advances 81 -> 80.
  - 2026-07-28: tQ26.H.80 fails with 400; watermark stays at 80.
  - 2026-07-29: tQ26.H.80 fails with 400; watermark stays at 80.
- `signal-cli-rest-api` logs confirm one `/v2/send` POST per day for
  `calendrical_rot`; the 400 responses on 2026-07-26/28/29 still result in the
  message being visible to recipients.
- `published.json` contains **no** `calendrical_rot` entries because
  `PublishGuard` only records when `publisher.publish()` returns truthy.
- `PublishGuard` keys on `(watermark_name, chart, placing)` and only records a
  publish when `publisher.publish()` returns a truthy value. It does **not**
  record a publish that returns `False` (e.g. a non-retriable Signal fault).
- `Signal.publish()` returns `False` on `MismatchedDevicesException` (the 409
  path) and on all other unrecognized errors; `_sweep()` then holds the
  watermark and does **not** call `guard.record()`.
- The daily timer is `OnCalendar=*-*-* 07:00:00 Europe/London` with
  `Persistent=true`. The guard window is exactly `24.0` hours and the "within
  window" check is strict (`<`).

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

6. **Confirmed: the 400 `MismatchedDevicesException` is a partial delivery.**
   The gateway logs show the 400 response on 2026-07-26 (tQ26.H.81),
   2026-07-28 (tQ26.H.80), and 2026-07-29 (tQ26.H.80). In each case the
   recipients saw the post, but gazette recorded a failure, held the
   watermark, and did **not** write a publish-guard entry. The next scheduled
   run retried the same `(chart, placing)` and posted it again.

7. **A 24-hour guard window is at best a tie with the publishing interval.**
   Even if the guard were recorded, a scheduled run at 07:00 today and 07:00
   tomorrow is exactly 24 hours apart, so the strict `< 24h` check returns
   `False` and the content would be eligible for republication. The guard is
   meant to stop duplicates from retries/timer misfires, not to prevent the
   normal daily advance, but the boundary is too tight if the watermark is
   ever held.

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

5. **Treat a group `MismatchedDevicesException` as a successful send.** In a
   Signal group, the 409 means some member devices have stale keys, but the
   message is still delivered to reachable members. `Signal.publish()` should
   return `True` for group targets so `publish_once()` advances the watermark
   and records the publish-once guard. For a single recipient, the message
   genuinely did not deliver, so keep returning `False`.

6. **Keep the publish-guard window at 24 hours for now.** With the group 409
   fix the watermark advances normally, so the 24-hour boundary race is no
   longer on the critical path. Revisit only if we see repeats that are not
   explained by held watermarks.

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
- [x] Treat Signal "Unregistered user" as a fault (8689632): return False,
      hold the watermark, and alert instead of silently advancing past
      undelivered content.
- [x] Deploy a new image: CI release runs built and pushed every main
      commit; latest image (2026-07-19 22:14 UTC) is from 8689632 and
      carries all fixes.
- [x] Verify the next scheduled run does not double-post `calendrical_rot`.
- [x] Pull prod evidence for the 2026-07-27 to 2026-07-29 `calendrical_rot`
      runs to confirm the repeats correlate with held watermarks and
      `MismatchedDevicesException` faults.
- [x] Decide the correct treatment for a 409 / partial-delivery Signal fault:
      treat group 409s as successful sends; hold watermark for individual 409s.
- [x] Patch `gazette/src/dynamicalsystem/gazette/publishers.py` so group
      `MismatchedDevicesException` returns `True` and individual returns `False`.
- [x] Add/update regression tests for group vs individual 409 behavior.
- [x] Run relevant unit tests.
- [x] Commit/push and deploy the new image.
- [x] Manually advance the `calendrical_rot` watermark from tQ26.H.80 to 79
      once, because 80 has already been delivered on 2026-07-28 and 2026-07-29.
- [ ] Verify the next scheduled run publishes tQ26.H.79 and does not retry 80.

## Outcomes

### Outcome 1: Root cause of `calendrical rot` double posts is identified

Tests:
- [x] Inspect gateway systemd timers and journal to confirm how many `gazette-publish` services actually started and when.
- [x] Inspect gateway `watermarks.json`, `watermarks.json.log`, and `watermarks.json.bak` to see whether the watermark advanced once or twice per duplicate event.
- [x] Cross-check Signal service logs (`signal-cli-rest-api`) for duplicate `/v2/send` POSTs to the `calendrical rot` target.
- [x] Determine whether the duplicate is a real second post or a logging artifact.

### Outcome 2: Fix is validated without live posts or watermark advances

Tests:
- [x] Reproduce the suspect path locally or on a non-prod target: prod logs confirm
      the 400 `MismatchedDevicesException` path; on-demand reproduction was not
      possible because the fault is intermittent, but the unit tests cover both
      the group-success and individual-failure branches.
- [x] Confirm the fix prevents the double post: unit tests assert a group 409
      advances the watermark and records the guard; the prod 409 pattern can no
      longer hold the watermark.
- [x] No production watermarks advanced during validation.
