loop: 07-quadlet-golive
closed: 2026-07-08
outcome: met -- gazette deployed on the OCI gateway as tinsnip quadlets; timed prod publishing is live

Key result: gazette.container (serve, health-gated, auto-updating) + gazette-publish.timer
(07:00 Europe/London) on gateway; on-box EnvironmentFile (SIGNAL_URL=http://signal:8080) +
watermark volume. CI->GHCR->auto-update->deploy Signal message proven end-to-end (v0.1.6).
First timed run 2026-07-08 07:00 UK published all 4 targets clean (watermarks decremented
abyss 99->98, others 100->99). Mac launchd disabled (no double-send); Signal send hardened
with 3x transient retry.
Closes the gazette cloud refactor (loops 01-07). Follow-on (separate arc): feature web
endpoints off the serve skeleton. Related: [[project_deploy_target]], [[project_local_deployment]].
