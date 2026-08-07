# Archived

- **Closed**: 2026-08-07 14:21 UTC
- **Status**: Succeeded
- **Summary**: Stopped the `calendrical rot` double-post regression by treating Signal group `MismatchedDevicesException` (HTTP 400 with StatusCode 409) as a successful partial delivery, adding a publish-once idempotency guard, serialising live sweeps with a non-blocking flock, and flipping the Signal retry policy to an allowlist of positively identified transient errors.
- **Outcomes**: 2/2 tests passed
- **Follow-up**: none
