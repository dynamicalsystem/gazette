# Loop 01: config module

Replace halogen's config and logging in gazette with a single minimal settings
module, and drop the `dynamicalsystem.halogen` dependency entirely.

## Why

halogen derives `namespace.package.module` from `__name__` and loads layered
env files with prefix-stripping (~170 lines to read two files). It also ships a
`SignalHandler` that posts WARNING+ logs to a live Signal service, coupling
application logging to running infrastructure. Both are cruft for a
run-to-completion cloud job. gazette should own a flat, explicit config.

## Scope

In:
- New `dynamicalsystem/gazette/config.py` exposing one settings object.
- Flatten the per-module env names (halogen's `PUBLISHERS_`/`CONTENT_`/
  `WATERMARKS_` prefixes) into one flat namespace.
- Replace `config_instance(__name__)` call sites in `content.py`,
  `publishers.py`, `watermarks.py`.
- Replace `from dynamicalsystem.halogen import logger` with a stdlib
  stdout logger; drop the Signal log handler.
- Remove the halogen dependency from `gazette/pyproject.toml`.

Out:
- Signal HTTP client changes (loop 2).
- Dockerfile/build changes (loop 3).
- OCI Vault wiring (loop 4) -- but the flat env names are chosen so Vault can
  map one secret bundle straight to environment variables.

## Config surface (what the code reads)

| Setting | Old env (halogen) | New env |
|---|---|---|
| github_url | CONTENT_GITHUB_URL | GITHUB_URL |
| github_token | CONTENT_GITHUB_TOKEN | GITHUB_TOKEN |
| bluesky_url | PUBLISHERS_BLUESKY_URL | BLUESKY_URL |
| bluesky_username | PUBLISHERS_BLUESKY_USERNAME | BLUESKY_USERNAME |
| bluesky_password | PUBLISHERS_BLUESKY_PASSWORD | BLUESKY_PASSWORD |
| signal_url | PUBLISHERS_SIGNAL_URL | SIGNAL_URL |
| signal_identity | PUBLISHERS_SIGNAL_IDENTITY | SIGNAL_IDENTITY |
| watermark_file | WATERMARKS_WATERMARK_FILE | WATERMARK_FILE |
| data_folder | derived from `<NS>_FOLDER` | DATA_FOLDER |
| environment | `<NS>_ENVIRONMENT` | ENVIRONMENT |
| log_level | LOG_LEVEL | LOG_LEVEL |

Dropped: LOG_SIGNAL_URL, LOG_SIGNAL_TARGET, LOG_SIGNAL_IDENTITY (no Signal logging).

Loading: local dev reads a `.env` via the settings module; cloud injects the
same names as real environment variables (Vault, loop 4).

## Outcomes and tests

### O1: gazette resolves config with no halogen import
- T1.1: `grep -r halogen gazette/src` returns nothing.
- T1.2: `grep -r halogen gazette/pyproject.toml` returns nothing; `uv sync` succeeds.
- T1.3: importing `dynamicalsystem.gazette` succeeds with halogen uninstalled.

### O2: logging goes to stdout only
- T2.1: a WARNING-level event is written to stdout and triggers no outbound
  HTTP POST to any Signal endpoint.
- T2.2: no `SignalHandler` / `SignalFormatter` remain referenced in gazette.

### O3: a dry-run publish works end to end locally
- T3.1: with a local `.env` and a `Validator` watermark, `gazette` logs a
  "Validator Publication - ..." line and decrements the watermark placing.

### O4: existing tests still pass
- T4.1: `make test` (pytests) passes after the env-name migration.

## Notes

The pytests currently rely on halogen's pytest-env defaults and the
`<package>.<env>.env` file layout. Migrating them to the flat names is part of
this loop (T4.1) -- expect to touch `pytests/.../environment.py` and the
`gazette.pytest.env` fixture.
