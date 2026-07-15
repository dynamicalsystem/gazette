---
loop: gazette-prod-guardrails
product: gazette
owner: dynamicalsystem
status: Observe
parent: null
blocked-by: []
worktrees: []
prs: []
triggers: []
---

# Gazette production publishing guardrails

## Status

Observe

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

## Decision

We will design and implement operational guardrails for gazette publishing that:

1. Make dry-run the default and prod mutation an explicit, logged opt-in.
2. Define and document when prod access is acceptable and how to recover
   watermark state.
3. Add code or process controls that prevent accidental multi-posting and
   watermark overruns.
4. Provide a non-prod integration path for validating publisher-specific
   behaviour.

## Action

- [x] Create this loop to capture the guardrail work.
- [ ] Enumerate candidate guardrails (CLI flags, env guards, rate limits,
      staging targets, watermark audit log, runbook).
- [ ] Evaluate each candidate against the observed failure modes and
      operational cost.
- [ ] Select and implement the smallest set of guardrails that prevents the
      observed incident.
- [ ] Document the watermark recovery procedure.
- [ ] Promote durable output to
      `architecture/docs/gazette-prod-guardrails/`.

## Outcomes

### Outcome 1: Prod mutation requires explicit opt-in

Tests:
- [ ] `gazette publish` defaults to Validator/dry-run and exits without posting
      to real targets.
- [ ] A prod publish requires an explicit flag or env var that is hard to set
      accidentally.
- [ ] The opt-in is logged at INFO or higher.

### Outcome 2: Watermark recovery is documented and safe

Tests:
- [ ] A runbook exists for advancing/resetting a prod watermark.
- [ ] The runbook includes a pre-check (verify current placing, chart, target)
      and post-check.
- [ ] Manual watermark changes leave an audit trail (log entry or versioned
      file).

### Outcome 3: Multi-post / overrun cannot happen silently

Tests:
- [ ] A single publish sweep cannot advance the same watermark twice for the
      same placing.
- [ ] A fault in one target does not cause duplicate posts in another target.
- [ ] Alerts are sent when a target fires more than once per expected window.
