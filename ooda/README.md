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
- Cloud config: OCI Vault -> environment variables.

## Loops

| # | Loop | Status | Outcome |
|---|------|--------|---------|
| 1 | [01-config-module](01-config-module/README.md) | [x] | gazette runs locally with no halogen import |
| 2 | [02-signal-http-client](02-signal-http-client/README.md) | [x] | gazette posts to the standalone Signal service |
| 3 | 03-build-from-source | [...] | `docker build .` runs the working tree, no PyPI release |
| 4 | 04-oci-vault-deploy | [...] | scheduled OCI run reads secrets from Vault, no keys on disk |
| 5 | 05-test-suite | [...] | suite runs offline with mocks; integration tests opt-in |

Loops 1-3 are testable entirely locally (dry-run). Loop 4 needs the VPS.

Loop 05 exists because the suite was found 10/5 red on `main` before any change:
the content fixture `tQ25.H` 404s and several tests hit live Bluesky/Signal. It
should split fast offline unit tests from opt-in integration tests.

## Open dependency

Loop 2 needs the Signal service contract: base URL/reachability, send endpoint
shape, sender identity ownership, auth, styled-text support, health endpoint.
