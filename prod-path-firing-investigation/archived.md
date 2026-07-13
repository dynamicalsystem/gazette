# Archived

- **Closed**: 2026-07-13 18:26 UTC
- **Status**: Succeeded
- **Summary**: Signal "duplicate" was a journald logging artifact; Bluesky silence was a code regression on long posts plus a missing source-side length gate. Fixed by enforcing Bluesky's 300-grapheme limit via ReviewInvalid, adding the same check to the content repo push gate, deploying a new image, and resetting the watermark.
- **Outcomes**: 6/8 tests passed (2 abandoned because the loop closed before the next scheduled run and 48-hour observation window).
- **Follow-up**: none
