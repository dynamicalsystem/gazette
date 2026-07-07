# [ARCHIVED] Loop 06: batch to service skeleton

Turn gazette from a run-to-completion batch into a long-lived web service, WITHOUT
coupling the publish path to the web path. The domain stays a library; `publish`
and `serve` become two thin, independent adapters over it.

## Status: [x] closed -- merged 2026-07-07 (7b4ee3d); see archived.md

## Why

Loop 05 puts an image on GHCR, but nothing on the `gateway` box can run it yet.
The target run model (ooda/README revised decisions) is a long-running FastAPI +
uvicorn service: it grows web endpoints later (historic reviews, insights,
festers integration) and its web server is the natural `HealthCmd` liveness
signal for `podman auto-update`. A batch job that exits 0 cannot be that.

But the publish sweep must NOT be welded into the web process. Our offline tests
and manual go-live sends (the loop-04 abyss run) have to work with no server up,
and a stuck publish must not degrade web responsiveness. So this loop factors the
domain into a shared library and hangs two thin adapters off it -- it does NOT add
an in-app scheduler. Timing is systemd's job in loop 07.

## Shape (settled)

```
        dynamicalsystem.gazette   (library: config, content, review,
                                    publishers, watermarks, publish_once)
                 /            \
   gazette publish (CLI)     gazette serve (FastAPI + uvicorn)
   -> publish_once()         -> /health now, web endpoints later
```

- `publish` is a thin caller of the LIBRARY, not of `serve`. `serve` is also a thin
  caller of the library. Neither imports the other; `publish` never boots the web
  stack, `serve` never runs the sweep on boot.
- Scheduling is out of the app entirely. Loop 07's systemd `.timer` decides what it
  pokes (a `gazette publish` one-shot container, or a `/publish` route) -- the code
  is identical either way because both go through the library.

## Scope

In:
- Extract the body of `__init__.py::main()` into a library function
  `publish_once() -> int` (the per-watermark sweep; behaviour unchanged).
- Rework the CLI into subcommands: `gazette publish` (== today's sweep, library-
  direct) and `gazette serve` (the service). Console script points at a dispatcher
  (`dynamicalsystem.gazette:cli`); update `__main__.py` to match.
- New `app.py`: FastAPI app with a lifespan and `GET /health` -> `200
  {"status":"ok","version": <pkg version>}`, deliberately independent of publish
  success, watermark state, and network. `gazette serve` runs uvicorn (bind
  `HTTP_HOST`/`HTTP_PORT`, default `0.0.0.0:8000`).
- Config additions (flat Settings): `http_host`, `http_port`.
- Deps (`gazette/pyproject.toml`): add `fastapi`, `uvicorn[standard]`. NOT apscheduler.
- `dockerfile`: keep `ENTRYPOINT ["gazette"]`, add `CMD ["serve"]` so the image
  serves by default; the one-shot is `podman run <img> publish`.
- Update `~/.local/bin/gazette-run.sh` (the transitional Mac launchd path) to call
  `gazette publish` explicitly.

Out:
- The systemd `.timer` + quadlets, and the trigger-style choice (one-shot container
  vs `/publish` route) -- loop 07.
- Real web feature endpoints (historic reviews / insights / random-listening /
  festers) -- separate arc. This loop ships ONLY `/health` as the skeleton.
- Test-suite repair (splitting offline units from live integration) -- separate.

## Outcomes and tests

### O1: the publish path is unchanged, factored behind a library function
- T1.1: `publish_once()` exists; `gazette publish` against a dev/Validator watermark
  logs the same `Validator Publication - ...` lines and decrements identically to
  the old bare `gazette`.
- T1.2: all loop 01-05 offline unit tests stay green (the entry rename does not
  break `create_publisher`/`main` call sites in tests).

### O2: serve boots and reports health, independent of publish
- T2.1: `gazette serve` starts uvicorn; `GET /health` -> 200 with `status` + the
  package `version`.
- T2.2: `/health` returns 200 with no watermark file present and no network
  reachable (liveness is not tied to content/publish).
- T2.3: booting `serve` fires NO publish and imports no publisher network client.

### O3: the two adapters are independent
- T3.1: `app.py` does not import `publish`/CLI code and does not call `publish_once`
  at import or boot; `publish` does not import `app`/fastapi.
- T3.2: `gazette publish` runs to completion with the server never started.

### O4: the image serves by default, one-shot still available
- T4.1: `podman run <img>` stays up and answers `GET /health` 200 (does not exit 0
  like the old batch).
- T4.2: `podman run <img> publish` runs the sweep against a mounted watermark file
  and exits (one-shot parity with loop 03).

### O5: no regression, still halogen-free
- T5.1: offline suite green; `grep -r halogen gazette/src` empty; new deps are only
  `fastapi` + `uvicorn`.

## Notes / risks

- The CLI change (bare `gazette` -> `publish`/`serve` subcommands) is an interface
  change. The only in-repo caller is `gazette-run.sh`; it is updated here. No implicit
  default subcommand -- an explicit `publish`/`serve` is clearer and more operable.
- `Watermark.update()` is a non-atomic read-modify-write. Fine for the one-shot; it
  becomes a real concern only if loop 07 chooses a `/publish` route that could be hit
  concurrently. Flagged for that decision, not fixed here.
- Deliberately no APScheduler/cron-in-container: on a systemd + podman box the
  scheduler is a `.timer` (visible in `systemctl list-timers`, per-run exit code in
  journald). Keeping timing out of the app is what keeps the two adapters uncoupled
  and the box troubleshootable.

## Result (2026-07-07)

Done and verified.

- Library: `publish_once()` extracted from the old `main()` (behaviour unchanged;
  added a guard so a missing/empty watermark file logs and returns 0 instead of
  crashing on `None` -- the loop-03 latent bug, in the function this loop touched).
- Adapters: `cli.py` (`gazette publish` / `gazette serve`, `serve` imported lazily
  so `publish` never pulls in fastapi); `app.py` (FastAPI, `GET /health` ->
  `{status, version}`, independent of watermark/content/network). Console script
  -> `:cli`; `__main__` -> `cli`.
- Config: `http_host`/`http_port`. Deps: `fastapi` + `uvicorn[standard]` only.
- dockerfile: `EXPOSE 8000`, `ENTRYPOINT ["gazette"]` + `CMD ["serve"]`.
  `gazette-run.sh` updated to `gazette publish` (local file, not in repo).

Verified: 17 offline unit tests green (6 new in test_service.py). Live `gazette
publish` dry-run posted place 98 x4 via Validator and decremented. Live `gazette
serve` -> `/health` 200 `{"status":"ok","version":"0.1.5"}`. Container: default
`podman run` serves and stays up (`/health` 200 in-container); `podman run <img>
publish` runs the one-shot and exits.

Out (unchanged): the systemd `.timer` + quadlets and the timer-trigger choice are
loop 07; feature endpoints are a separate arc.
