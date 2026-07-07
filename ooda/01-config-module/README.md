# [ARCHIVED] Loop 01: config module

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

### O4: no regression in the existing suite
- T4.1: the locally-runnable tests that passed before still pass; no new
  failures introduced by the config migration.

## Result (2026-06-26)

Done and verified.

- New modules: `config.py` (pydantic-settings flat `Settings`), `log.py`
  (stdout-only logger), `utils.py` (vendored `url_join`/`possessive`/
  `cli_hyperlink`). halogen removed from `gazette/pyproject.toml`; `uv sync`
  uninstalled it. All call sites rewired.
- New unit tests in `pytests/.../test_config.py` (flat env, defaults,
  no-halogen import) -- all green.
- Test fixture `environment.py` now supplies the flat names for local-only,
  non-secret config (data folder, watermark file, public content URL).

### Baseline finding: the integration suite is pre-broken

Before any change, `make test` was 10 failed / 5 passed on `main` -- NOT caused
by this work:

- The test content chart `tQ25.H.json` 404s on the GitHub content repo, so every
  `content` test crashes in `review.py` on a `None` item.
- `test_bluesky` / `test_signal_*` do real logins and real sends.

After loop 1: 10 failed / 8 passed (the same 10 integration failures, plus the 3
new config tests). So loop 1 is net-non-regressing. Repairing the integration
suite (test fixture data in the content repo + mocking live services) is its own
loop -- see ooda/README.md loop 05.

### Pre-existing bugs noticed (left for their own fix)

- `content.py:36` missing f-string in `logger.error("{response.text} ...")`.
- `publishers.py:131` broken `%` format and uses `print` not the logger.
- `publishers.py:168` `_messages()` uses `self.watermark["target"]` but
  `Watermark` is an object (`.target`).
- `__init__.py` `main()` iterates `watermarks()` which can return `None`.
