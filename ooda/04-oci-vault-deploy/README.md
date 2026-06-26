# Loop 04: deploy + config delivery

Get gazette running unattended on OCI with secrets from Vault. Precursor work
(done first, locally): give the halogen-free code a working flat-config delivery
for local prod + dev, so we can iterate toward 26.H before the cloud move.

## Status: [~] in progress

Local config delivery is staged and verified. Cloud (OCI Vault, VPS scheduler,
compose rewrite, watermark volume) is not started.

## Config delivery model (local, 2026-06-26)

The new code reads flat env vars; `.env` (CWD) for dev, exported vars for prod.
pydantic-settings precedence (env vars > .env) is the mechanism that keeps prod
and dev from colliding even though both run from the repo dir.

| Path | Source | Watermarks | Publishers |
|---|---|---|---|
| dev (`uv run gazette`) | repo `.env` (gitignored) | `watermarks.dev.json` | Validator (dry run) |
| prod (launchd runner) | `gazette.prod.env`, sourced `set -a` | `watermarks.prod.json` | Signal / Bluesky |

Verified: dev `.env` -> `env=dev wm=watermarks.dev.json`; runner-style exported
prod vars override it -> `env=prod wm=watermarks.prod.json`; dev watermarks
resolve to the 4 routes; runner passes `bash -n`.

## Staged artifacts (local, not in repo)

- `gazette/.env` -- flat dev config (gitignored), Validator-default.
- `~/.local/share/dynamicalsystem/config/gazette.prod.env` -- migrated to FLAT
  names; ENVIRONMENT=prod, WATERMARK_FILE=watermarks.prod.json.
- `~/.local/share/dynamicalsystem/data/watermarks.dev.json` -- rewritten
  Validator-only across all 4 routes (the old live `signal_to_abyss` footgun is
  gone). chart tQ25.H, placing 100, for a real dry run.
- `~/.local/share/dynamicalsystem/data/watermarks.tQ26.H.template.json` -- the
  go-live set (real Signal/Bluesky routes, placing 100). Inert until copied over
  `watermarks.prod.json`.
- `~/.local/bin/gazette-run.sh` -- sources the flat prod env; old
  DYNAMICALSYSTEM_* exports removed.

## Readiness for tQ26.H

| Need | Status |
|---|---|
| Nothing required from the NAS (run path fully local) | done |
| Flat config delivery (dev + prod) | done, verified |
| Dev dry-run path is Validator-only (safe) | done |
| tQ26.H go-live template ready | done |
| Content GitHub PAT | BLOCKER -- expired ~2026-06-24, regenerate |
| End-to-end dry run proves the pipeline | pending the PAT |

## Next

1. Simon: regenerate fine-grained PAT (repo `DynamicalSystem/content`,
   Contents: Read-only), paste into `.env` + `gazette.prod.env`.
2. Dry-run `uv run gazette` (dev) against tQ25.H through Validator -> prove
   content fetch + format + watermark decrement with zero real sends.
3. When tQ26.H drops: `cp watermarks.tQ26.H.template.json watermarks.prod.json`.
4. Then the actual cloud loop: compose rewrite (drop in-repo signal + NFS),
   OCI Vault via instance principal, VPS scheduler, watermark volume.
