# Loop 07: tinsnip quadlet + go-live

Deploy gazette to the `gateway` box as tinsnip quadlets -- a long-lived `serve`
container plus a timer-driven `publish` one-shot -- and cut tQ26.H publishing over
from the Mac to the box.

## Status: [...] not started

## Why

Loop 05 put the image on GHCR; loop 06 made it service-shaped (serve + one-shot
publish). Nothing on the box runs it yet -- there is no `gazette.container` in
tinsnip (only caddy, festers, signal-cli-rest-api). This loop adds the units so
`podman auto-update` pulls and runs gazette like every other service, and moves
publishing off the Mac launchd path.

## Shape (from loop 06)

One image, two systemd units, per the settled design:

- `gazette.container` -- long-lived `gazette serve`; the health-gated web surface.
- `gazette-publish.container` + `.timer` -- one-shot `gazette publish` on an
  `OnCalendar=`. systemd is the scheduler; no in-app cron.

Open decision to make here, with real units in front of us: the timer runs the
`gazette publish` one-shot container (leaning this -- isolated, own exit code in
journald), OR curls a `/publish` route on the serve container. Code is identical
either way (both go through the library).

## Scope

In (all in the private `tinsnip` repo, `hosts/gateway/`):
- `gazette.container`: image `ghcr.io/dynamicalsystem/gazette:latest`; `Exec`/CMD
  `serve`; on `signal-net` + `web`; `EnvironmentFile=` (chmod 600, gitignored);
  watermark volume mounted at `/data`; `HealthCmd` hitting `/health`;
  `AutoUpdate=registry`; published/proxied via caddy if the web surface is public.
- `gazette-publish.container` + `gazette-publish.timer`: `Exec`/CMD `publish`; same
  image + `EnvironmentFile` + watermark volume; `OnCalendar=` cadence; no port.
- On-box `EnvironmentFile`: the flat prod config. NOTE `SIGNAL_URL=http://signal:8080`
  (the container name on `signal-net`) -- NOT the Mac WireGuard address `10.100.0.1:8010`.
  Secrets (GITHUB_TOKEN read-only PAT, BLUESKY_PASSWORD app password) live here, not
  Vault (loop-04 decision).
- Watermark volume seeded from the current `watermarks.prod.json` so the box picks up
  the chart at the right placing (abyss is mid-flight at 99 after the 2026-07-01/07
  sends; other targets not yet started).
- Cutover: disable the Mac launchd + `gazette-run.sh` publish path so only the box
  publishes.

Out:
- Feature web endpoints (historic reviews / insights / festers) -- separate arc.
- Test-suite repair (offline vs live split) -- separate.

## Outcomes and tests

### O1: serve runs on the box, health-gated
- T1.1: `systemctl --user status gazette` active; `curl localhost:<port>/health` on
  the box returns 200; the auto-update health gate passes.

### O2: the publish timer fires and publishes to the real targets
- T2.1: `systemctl --user list-timers` lists `gazette-publish`; a manual
  `systemctl --user start gazette-publish.service` sends the next placing to the
  configured targets and `journalctl -u gazette-publish` shows exit 0 + the
  `Published - ...` lines.

### O3: auto-update pulls new images
- T3.1: a subsequent GHCR push is pulled by `podman-auto-update.timer` within its
  interval; the serve container restarts on the new digest; health holds.

### O4: config and state are correct and isolated
- T4.1: `EnvironmentFile` present (chmod 600, gitignored); `SIGNAL_URL=http://signal:8080`
  resolves on `signal-net`; the watermark volume persists across container restarts.

### O5: exactly one publisher -- no double-send
- T5.1: the Mac launchd publish path is disabled; the box is the only thing that
  advances the (single, box-resident) watermark; a placing is sent once per run.

## Risks / watch items

- Double-publish: the Mac and the box use DIFFERENT watermark files, so if both run
  they both send. Retiring the Mac launchd path is a hard prerequisite of go-live,
  not a nicety.
- Watermark seed/migration: get the box volume's `watermarks.prod.json` to the exact
  current placings before enabling the timer, or the chart re-sends or skips.
- `Watermark.update()` is a non-atomic read-modify-write; if the trigger becomes a
  `/publish` route that could overlap, add a guard (see loop 06 note).
- `SIGNAL_URL` differs by environment (on-box `signal:8080` vs Mac WG) -- the
  EnvironmentFile, not the repo, carries the box value.

## Depends on

- 05 (GHCR image), 06 (service shape). Needs the `gateway` box + `tinsnip` access.
  Reference: `../tinsnip` (`hosts/gateway/festers.container` as the template).
