# OODA: gazette cloud refactor

Refactor gazette so it runs on an Oracle Cloud (OCI) server and can be developed
locally at all times, with no dependency on the NFS NAS, tailscale, or the cloud
gateway experiment.

## Target architecture

gazette becomes a self-contained, run-to-completion publisher:

- Config: own minimal settings module. Local dev reads a `.env`; cloud reads
  from OCI Vault, injected as environment variables.
- Logging: stdout only. The Signal log handler (in halogen) is dropped.
- Signal: gazette no longer owns signal-cli. It calls a separate Signal service
  (its own repo) over HTTP. gazette is just one client.
- Build: from local source, no PyPI release in the deploy path.
- State (watermarks): a JSON file on a persistent volume (VPS local disk on
  cloud; repo/local path for dev).
- Content: GitHub raw JSON (unchanged, already remote).

Local dev uses the `Validator` (dry-run) publisher, so it never touches the prod
Signal identity or any NAS.

## Decisions (settled 2026-06-26)

- halogen: replace it in gazette with a minimal config module; drop the dependency.
- Local dev: dry-run (Validator) only; no local signal-cli needed.
- Signal identity: lives in a separate Signal service/repo. gazette gets only the
  HTTP contract (URL, send endpoint, sender, auth) via config.
- Cloud config: OCI Vault -> environment variables.  [SUPERSEDED 2026-07-01]

## Decisions (revised 2026-07-01) -- commit to OCI + podman + quadlets

The deploy target is now the tinsnip model, not a bespoke compose/Vault setup.
tinsnip (`github.com/dynamicalsystem/tinsnip`, private) is the source of truth for
what runs on each box as rootless podman **Quadlet** systemd units; images are
built by each service's own CI to GHCR and pulled by `podman auto-update`. The
box is `gateway` (OCI Ampere), already running caddy + festers + signal-cli-rest-api
on the `web` and `signal-net` networks. Reference: `../tinsnip`, `../festers`.

- Config delivery: on-box `EnvironmentFile=` (chmod 600, gitignored), NOT Vault.
  gazette has only TWO secrets (GITHUB_TOKEN read-only PAT, BLUESKY_PASSWORD app
  password) -- both revocable, low blast radius. Vault plumbing is disproportionate
  and would be the only non-uniform service on the box. Vault stays on the shelf
  for when we hold real secrets. Loop 04's Vault plan is dropped.
- Run model: gazette becomes a LONG-RUNNING FastAPI + uvicorn service (matches
  festers' stack), NOT a run-to-completion batch job. Rationale: it will grow web
  endpoints (historic reviews, insights, random-listening, festers integration).
  The web server is also the natural `HealthCmd` liveness signal for the
  auto-update health gate.
- Publisher stays decoupled: the scheduled publish runs on an internal scheduler
  (APScheduler async) inside the app lifespan, but a one-shot `gazette publish` CLI
  is retained so dry-run/Validator tests and the loop-01..03 offline tests never
  need to stand up a web server. Firm convention.
- prod `SIGNAL_URL = http://signal:8080` (container name on signal-net). The
  WireGuard address `http://10.100.0.1:8010` is DEV-from-Mac only (see the
  project_signal_over_wireguard memory).
- Legacy `docker-compose.yml` + `deploy.sh` (old homelab, `kalmanfilter` net, from
  the tangled.sh tinsnip) are to be deleted. Merged origin/main (8 legacy commits)
  into local main on 2026-07-01 -- unpushed; push at the end of loop 05 after the
  deletion so we don't publish-then-delete.

## Loops

Loops 01-07 are all closed and archived (each folder has an archived.md and an
[ARCHIVED] README heading, so /readthedocs skips them). **The gazette cloud
refactor is COMPLETE** -- gazette runs on the OCI `gateway` box as tinsnip
quadlets, publishing tQ26.H daily at 07:00 UK (first timed run 2026-07-08). No
active loop. Feature web endpoints (historic reviews / insights / festers) are a
separate future arc off the loop-06 serve skeleton.

| # | Loop | Status | Outcome |
|---|------|--------|---------|
| 1 | [01-config-module](01-config-module/README.md) | [x] | gazette runs locally with no halogen import |
| 2 | [02-signal-http-client](02-signal-http-client/README.md) | [x] | gazette posts to the standalone Signal service |
| 3 | [03-build-from-source](03-build-from-source/README.md) | [x] | `docker build .` runs the working tree, no PyPI release |
| 4 | [04-oci-vault-deploy](04-oci-vault-deploy/README.md) | [x] | local flat-config delivery done + verified; PAT/Signal/WG path proven end-to-end (real abyss send). Vault half dropped -- see revised decisions. |

Loops 1-4 are testable entirely locally (dry-run). Phase 2 needs the `gateway` box.

## Phase 2 loops (OCI + quadlets) -- not started

| # | Loop | Depends | Outcome |
|---|------|---------|---------|
| 05 | [CI -> GHCR + drop legacy](05-ci-ghcr/README.md) `[x]` | none | gazette CI builds multi-arch (arm64) `ghcr.io/dynamicalsystem/gazette:latest`; `docker-compose.yml`/`deploy.sh` deleted; main pushed |
| 06 | batch -> service skeleton | none | FastAPI + uvicorn app with `/health`; publisher behind an internal APScheduler; one-shot `gazette publish` CLI retained; offline tests still pass |
| 07 | tinsnip quadlet + go-live | 05, 06 | `hosts/gateway/gazette.container`: EnvironmentFile, on signal-net + web, watermark volume, HealthCmd, AutoUpdate=registry, SIGNAL_URL=http://signal:8080 |
| -- | test-suite repair | any | split fast offline units from opt-in integration (was old loop 05). Note: `tQ25.H` NO LONGER 404s (content published since); remaining issue is tests hitting live Bluesky/Signal. |
| -- | feature endpoints (separate arc) | 06 | historic reviews / insights / random-listening / festers integration -- each its own loop. "Historic reviews" first needs a data-source decision (today content is fetched per-run per-chart from GitHub raw; serving history needs a store or enumeration). |

## Go-live readiness (tQ26.H)

PAT [x] regenerated + working. Signal path + WireGuard [x] proven (real abyss send
2026-07-01). Remaining blocker: tQ26.H content not yet published (still 404). When
it drops: `cp watermarks.tQ26.H.template.json watermarks.prod.json` then run.
