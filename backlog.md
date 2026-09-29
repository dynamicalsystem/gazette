# Backlog

Cross-loop triggers and observations that outlive their owning loops.

## Triggers

- [x] when: PR #6 (gazette-prod-guardrails) merges
      then: "Update the tinsnip Quadlet timer unit to pass --live and set GAZETTE_LIVE=1 before the next image deploy"
      resolved: 2026-07-15 UTC

## Observations

- 2026-09-29 gazzette|content|festers: update songkick with buy rated acts.
- 2026-09-12 gazette: a `gazette publish --only <route>` flag would let a
  manual run post to one route (e.g. Abyss) without touching the others. Raised
  in abyss-lead-invariant as a way to restore a lead by posting rather than
  skipping. Not needed while the follows rule self-heals.
- 2026-09-26 gazette: each sweep logs `Loaded watermark - abyss` three extra
  times, once per follower, so the follows rule re-reads the leader from disk
  for every follower. Harmless at four routes; worth a single read per sweep
  if routes multiply. Seen closing abyss-lead-invariant.
