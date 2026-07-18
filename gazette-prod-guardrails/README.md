---
loop: gazette-prod-guardrails
product: gazette
owner: dynamicalsystem
status: Act
parent: null
blocked-by: []
worktrees: []
prs:
  - https://github.com/dynamicalsystem/gazette/pull/6
triggers:
  - when: PR #6 merges
    then: "Update the tinsnip Quadlet timer unit to pass --live and set GAZETTE_LIVE=1 before the next image deploy"
---

# Gazette production publishing guardrails

## Status

Act

**Owner:** dynamicalsystem

## Context

On 2026-07-13, a live publishing incident burned down multiple gazette reviews
in a single day. The immediate delivery bugs were fixed and the loop closed in
`prod-path-firing-investigation`, but the response pattern itself was unsafe:
prod was used as the test environment, watermarks were advanced manually, and
fixes were validated by posting live content to real users. This loop designs
operational guardrails so that cannot happen again.

## Observations

- `prod-path-firing-investigation` fixed Bluesky and Signal delivery bugs and
  closed on 2026-07-13.
- During that incident, multiple manual prod runs were executed in "yolo" mode
  with prod credentials.
- The AI assistant iterated directly on prod until the bugs were fixed, rather
  than isolating changes.
- Fixes were validated by posting real content to real targets (Signal groups,
  Bluesky, Abyss).
- Watermarks for multiple targets advanced in one day, consuming reviews
  intended for subsequent days.
- The Abyss target is supposed to lead the Josh and Calendrical Rot targets by
  one day so tomorrow's output can be proofed, but is now at the same watermark.
- A manual watermark adjustment is required to restore the intended lead.
- The codebase already supports dry-run via the `Validator` publisher, but it
  does not catch all prod-only failure modes (e.g., Bluesky grapheme limit,
  Signal formatting).
- There is no documented runbook for recovering from a watermark overrun or for
  deciding when prod mutation is acceptable.

## Orientation

1. **The default path must be safe.** Any publishing command that can mutate
   prod should require an explicit opt-in. Dry-run / `Validator` should be the
   obvious and frictionless default.
2. **Prod is not a test environment.** Validating fixes by posting to real users
   violates the "low regard for users" threshold. We need a non-prod integration
   path (staging targets, canary recipients, or explicit human approval) for
   changes that cannot be verified offline.
3. **Watermarks are production state.** Manual edits to prod watermarks must be
   rare, documented, and reversible. The current file-based state has no audit
   trail.
4. **Pressure amplifies bad assumptions.** When a bug is live, the fastest fix
   feels like iterating directly on prod. Guardrails must add enough friction
   that the safer path is faster than the risky one.
5. **Tooling and process both failed.** The AI assistant assumed prod iteration
   was acceptable because the tooling allowed it and there was no explicit
   instruction or friction saying otherwise. Guardrails that rely only on a
   runbook will fail under pressure; the default code path must enforce safety.

### Candidate guardrails

| Guardrail | Cost | Prevents | Notes |
|---|---|---|---|
| **A. Default `gazette publish` to Validator** | Low code, medium habit change | Accidental prod posts from CLI | Scheduled prod run must pass `--live`. Breaks current default. |
| **B. Explicit prod opt-in env var** | Low code | Accidental prod credential use | E.g. `GAZETTE_LIVE=1` required by non-Validator publishers. Harder to set accidentally than a CLI flag. |
| **C. Watermark publish-once guard** | Medium code + new state | Duplicate posts and watermark overruns | Track `(watermark, placing)` pairs already published. Refuse repeats within a window. |
| **D. Per-target rate limit / cooldown** | Low-medium code | Burn-down of multiple reviews in one day | Reject publish if target already fired within N hours. Configurable window. |
| **E. Canary / staging targets** | Medium ops | Need to test real publishers | Separate Signal group / Bluesky test account for integration validation. Adds ongoing account maintenance. |
| **F. Watermark backup + audit log** | Low-medium code | Undocumented, irreversible watermark changes | Snapshot `watermarks.json` before update; append a log line with who/what/when. |
| **G. Operational runbook** | Low code, high discipline | Ad-hoc prod access and recovery | Document when prod mutation is allowed, how to advance/reset watermarks, and how to validate safely. |
| **H. Project instructions for AI** | Very low | AI assuming prod iteration is OK | Add explicit guardrails to `AGENTS.md` or similar: "never iterate on prod; default to dry-run; require human confirmation for live posts." |

### Evaluation

- **A + B together** are the highest-leverage code changes. A makes the safe
  path the default; B makes prod access a deliberate, logged act. Either alone
  has gaps (A can be bypassed by a script that passes `--live`; B can be bypassed
  by setting the env var and running the existing default command). Together
  they force two explicit choices.
- **C** is valuable but adds the most complexity and a new failure mode (what
  happens when the guard state drifts?). Consider deferring until after A/B/F/G
  are in place, unless the daily scheduled run is also at risk of double-firing.
- **D** is simpler than C and directly prevents the observed burn-down. A 20-hour
  cooldown per target would have blocked the extra posts while still allowing the
  normal daily schedule. The trade-off is emergency recovery: if a legitimate
  fix needs to go out the same day, an operator must deliberately clear the
  cooldown.
- **E** is the right long-term answer for validating publisher-specific fixes,
  but it requires owning and maintaining test accounts. It is worth doing only
  if we expect frequent publisher-side changes.
- **F** is cheap insurance and supports both normal operation and recovery. It
  should be paired with a documented restore procedure.
- **G** is necessary regardless of code changes. It is where we write down the
  "when prod access is acceptable" rule and the watermark recovery steps.
- **H** directly addresses the AI behaviour but does nothing for a human
  operator. It is worth adding because the incident involved an AI assistant,
  but it is not a substitute for code guardrails.

### Recommended first cut

Implement **A, B, F, G, H** as the minimal set that prevents the observed
incident without over-engineering. Defer **C** and **D** unless the scheduled
daily run shows it is also vulnerable to double-firing. Keep **E** as a backlog
item for when publisher integration testing becomes routine.

## Decision

We will implement the first cut now: guardrails **A, B, F, G, H**.

### 1. Default `gazette publish` to dry-run (A)

- `gazette publish` with no flags runs every configured watermark through the
  `Validator` publisher. It logs what would be published but does not post to
  Signal, Bluesky, or any other live target.
- `gazette publish --live` opts in to real publishers, but only if the env guard
  is also satisfied (see #2).
- `gazette serve` is unchanged; it does not trigger publishes and needs no
  opt-in.

### 2. Env guard for live publishers (B)

- Non-Validator publishers refuse to initialise unless `GAZETTE_LIVE=1` is set
  in the environment.
- `gazette publish --live` without `GAZETTE_LIVE=1` exits with a clear error and
  does not load credentials.
- The Quadlet timer unit (`gazette-publish.timer`) is the only routine
  process that should run with live publishers. It must be updated to pass both
  `--live` and `GAZETTE_LIVE=1`; see the coordination note below.

### 3. Watermark backup + audit log (F)

- Before `Watermark.update()` writes `watermarks.json`, copy it to
  `watermarks.json.bak` in the same directory.
- Append a line to `watermarks.log` in the same directory with:
  `YYYY-MM-DDTHH:MM:SSZ watermark=<name> old=<chart>.<old> new=<chart>.<new>`.
- The backup is intentionally a single file; in a panic, the operator knows
  exactly where to find the last known-good state.

### 4. Operational runbook (G)

- Create `docs/runbooks/prod-publishing.md` in the repo covering:
  - How to validate a change with `gazette publish` (dry-run).
  - When live prod access is permitted and who must approve.
  - How to advance or reset a watermark safely using the existing code.
  - How to restore `watermarks.json` from `watermarks.json.bak`.

### 5. Project AI instructions (H)

- Create `/work/AGENTS.md` (project-scope) that preserves the existing user-scope
  rules and adds a "Production publishing" section requiring:
  - Default to dry-run / `Validator` for any publish command.
  - Explicit human confirmation before any live post or prod watermark change.
  - No iteration on prod; isolate and reproduce offline or in a non-prod target.

## Action

- [x] Create this loop to capture the guardrail work.
- [x] Enumerate candidate guardrails and evaluate them against the incident.
- [x] Decide exact CLI/env interface for the prod opt-in.
- [x] Implement default-dry-run in `gazette publish`.
- [x] Implement `GAZETTE_LIVE=1` env guard for non-Validator publishers.
- [x] Add watermark backup + audit log around `Watermark.update()`.
- [x] Write `docs/runbooks/prod-publishing.md`.
- [x] Create `/work/AGENTS.md` with production publishing guardrails.
- [x] Add/update tests for the new opt-in and watermark audit behaviour.
- [x] Open PR #6 with the guardrail changes.
- [ ] Merge PR #6.
- [ ] Update tinsnip Quadlet unit to pass `--live` and set `GAZETTE_LIVE=1`.
- [ ] Promote durable output to
      `architecture/docs/gazette-prod-guardrails/`.

## Outcomes

### Outcome 1: Prod mutation requires explicit opt-in

Tests:
- [x] `gazette publish` defaults to Validator/dry-run and exits without posting
      to real targets.
- [x] `gazette publish --live` without `GAZETTE_LIVE=1` exits with an error.
- [x] `GAZETTE_LIVE=1 gazette publish --live` uses real publishers as configured.
- [x] The opt-in is logged at INFO or higher.
- [ ] The scheduled timer unit sets both the flag and the env var intentionally.

### Outcome 2: Watermark recovery is documented and safe

Tests:
- [x] `docs/runbooks/prod-publishing.md` exists and covers dry-run, live access,
      watermark advance/reset, and backup restore.
- [x] Every `Watermark.update()` creates `watermarks.json.bak` and appends to
      `watermarks.log`.
- [ ] Restoring from `watermarks.json.bak` returns the watermark file to the
      previous state. (Verified by unit test; not yet exercised in prod.)

### Outcome 3: Multi-post / overrun cannot happen silently

Tests:
- [x] A deliberate double-run of `gazette publish` is blocked or warned by the
      prod opt-in, not by publisher-specific behaviour.
- [ ] Alerts are sent when a target fires outside its expected window.

### Outcome 4: AI assistants do not iterate on prod

Tests:
- [x] `/work/AGENTS.md` explicitly requires human confirmation before any live
      post or prod watermark change.
- [x] Instructions require dry-run validation before any prod mutation.
