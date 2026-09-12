# Backlog

Cross-loop triggers and observations that outlive their owning loops.

## Triggers

- [x] when: PR #6 (gazette-prod-guardrails) merges
      then: "Update the tinsnip Quadlet timer unit to pass --live and set GAZETTE_LIVE=1 before the next image deploy"
      resolved: 2026-07-15 UTC

## Observations

- 2026-09-12 gazette: a `gazette publish --only <route>` flag would let a
  manual run post to one route (e.g. Abyss) without touching the others. Raised
  in abyss-lead-invariant as a way to restore a lead by posting rather than
  skipping. Not needed while the follows rule self-heals.
- 2026-09-12 gazette: `gazette publish` (dry-run) advances watermarks.
  `Validator.publish` returns True and the sweep updates the watermark in
  every mode. The prod runbook recommends a dry-run on the gateway before a
  live run, which would decrement every prod watermark. Verification in
  abyss-lead-invariant used a copy of the data folder. Warrants a loop: either
  dry-run must not update, or the runbook must say to use a copy.
