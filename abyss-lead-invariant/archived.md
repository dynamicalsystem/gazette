# Archived

- **Closed**: 2026-09-26 12:00 UTC
- **Status**: Succeeded
- **Summary**: A data-declared `follows` rule now holds a follower until its leader has published the placing; deployed 2026-09-12, it restored Abyss's lead over Josh at the 09-13 sweep without a manual bump and held through 14 sweeps with zero violations.
- **Outcomes**: 12/13 tests passed, 1 abandoned (the manual-bump log entry, because no bump was needed).
- **Follow-up**: dry-run-no-advance (closed, PR #8). Backlog: `gazette publish --only <route>`; leader watermark reloaded per follower.
