# [ARCHIVED] Loop 02: signal HTTP client

Make gazette's Signal boundary correct, safe, and documented for both prod and
dev, talking to the standalone Signal service (its own repo) over HTTP.

## Why

Signal moved to its own repo. gazette is just one HTTP client of it. After loop
01 the publisher already reads `SIGNAL_URL` from env and posts the bbernhard
`/v2/send` signature, so "migrate prod->dev" is a config change, not a code
change. What remained was an unconfigured env contract, a missing safety net,
and one genuinely broken code path.

## Signal service contract (from the Signal-service owner, 2026-06-26)

- Send: `POST {SIGNAL_URL}/v2/send` with
  `{message, text_mode:"styled", number:<sender>, recipients:[<target>]}`.
  Identical signature in prod and dev.
- Sender: gazette passes `number` = `SIGNAL_IDENTITY` (the real gigbot account
  `+447377115354`).
- Auth: none -- the API is host-only / private-network; reachability is the
  control, not a token.
- Reachability:
  - prod: `http://signal:8080` (DNS alias on the shared `signal-net`).
  - dev (gazette in a podman container on the Mac): `http://host.containers.internal:8010`.
  - dev (gazette run directly on the Mac host): `http://127.0.0.1:8010`.
  - dev reaches the host-only cloud API via an SSH tunnel:
    `ssh -i ~/.ssh/id_oci -N -L 8010:127.0.0.1:8010 ubuntu@152.67.153.4`

## Scope

In:
- `.env.example` documenting the full flat config incl. the prod/dev `SIGNAL_URL`
  values and the dev tunnel. (It did NOT previously exist in this repo.)
- `.gitignore`: ignore `.env` / `.env.*`, keep `.env.example` tracked.
- Fix the broken 400-retry path in `Signal.publish` / rename `_messages` ->
  `_drain_inbox`: it subscripted `self.watermark["target"]` (an object) and read
  `self.config.signal_phone_number` (nonexistent) and double-`len()`d. Now drains
  `{SIGNAL_URL}/v1/receive/{SIGNAL_IDENTITY}` and retries.
- Replace the broken `print("...: %", ...)` with a real logger line.
- Fix the vendored `url_join` trailing-slash wart (it forced `/v2/send/`); drop
  the `[:-1]` workaround in `content.py`.
- Mocked unit tests for the Signal contract and the drain-retry path
  (`test_signal_client.py`) plus `url_join`/`possessive` (`test_utils.py`).

Out:
- Live send verification (would fire real Signal messages -- see dev safety).
- Repairing the integration suite (loop 05).

## Dev safety (decision)

Dev calls go to the real gigbot account; a `Signal` watermark pointed at a real
group sends real messages the instant gazette runs. Convention: **dev watermarks
use the `Validator` publisher (logs only), or target your own number.**

Heads-up recorded: the on-disk `watermarks.dev.json` (runtime data, not in repo)
currently contains a live `Signal` -> real abyss group entry alongside the
`Validator` one. That should be removed or retargeted before running gazette in
dev against the tunnel.

## Outcomes and tests

### O1: Signal publish hits the configured service with the right contract
- T1.1: `test_signal_client.py::test_signal_publish_posts_expected_contract`
  asserts POST to `{SIGNAL_URL}/v2/send` with number/recipients/text_mode and a
  spoiler-wrapped verdict.

### O2: the 400 "regularly received" path drains and retries instead of crashing
- T2.1: `test_signal_client.py::test_signal_publish_drains_and_retries_on_400`
  asserts one drain GET to `/v1/receive/{identity}` and a second send.

### O3: url_join produces canonical URLs
- T3.1: `test_utils.py::test_url_join_no_trailing_slash` / `test_url_join_tolerates_slashes`.

### O4: no regression
- T4.1: full suite 10 failed / 13 passed (same 10 pre-existing integration
  failures; +5 new loop-02 tests pass).

## Result (2026-06-26)

Done and verified. Migration prod<->dev is now purely setting `SIGNAL_URL`.
