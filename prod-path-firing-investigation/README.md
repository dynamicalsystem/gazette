---
loop: prod-path-firing-investigation
product: gazette
owner: dynamicalsystem
status: Observe
parent: null
blocked-by: []
worktrees: []
prs: []
triggers: []
---

# Production path firing investigation

## Status

Observe

**Owner:** dynamicalsystem

## Context

Production delivery paths are showing inconsistent firing behaviour. The Signal
path produced duplicate output this morning, while the Bluesky path has stopped
firing entirely. This loop exists to determine whether the failures share a root
cause or are independent incidents, and to restore reliable delivery on both
paths.

## Observations

- Signal path fired twice on the morning of 2026-07-13.
- Bluesky path has not fired for approximately three days (since around 2026-07-10).
- The two paths are part of the same production gazette delivery pipeline.

## Orientation

Two distinct failure patterns are visible:

1. **Signal path:** duplicate firing suggests a duplicated trigger, missing
   idempotency key, or a scheduling/queue retry that was not de-duplicated.
2. **Bluesky path:** complete absence of firing for three days suggests a path
   failure, authentication or credential issue, rate-limit block, or an upstream
   source that is no longer yielding items for this destination.

Possible shared causes (to validate or rule out):

- A common scheduler or dispatch component affecting both paths differently.
- A recent deployment, configuration change, or secret rotation that touched
  both integrations.
- Shared infrastructure (queue, worker, network egress) with path-specific
  symptoms.

## Decision

To be determined after further observation and data gathering.

## Action

- Collect timestamps and delivery logs for both paths.
- Identify the last successful Bluesky firing and any failure signals since then.
- Identify the exact Signal duplicate event and compare it with normal single
  firings.
- Check for recent deployments, config changes, or secret rotations.

## Outcomes

### Outcome 1: Signal path fires exactly once per intended event

Tests:
- [ ] Root cause of duplicate Signal firing is identified.
- [ ] Fix is applied and verified in production.
- [ ] No duplicate Signal firings observed for 48 hours after the fix.

### Outcome 2: Bluesky path resumes reliable firing

Tests:
- [ ] Root cause of Bluesky silence is identified.
- [ ] Fix is applied and verified in production.
- [ ] Bluesky path fires successfully at least once after the fix.
- [ ] Bluesky path continues to fire normally for 48 hours after recovery.
