from os import environ
from pathlib import Path
from pytest import fixture
from unittest import mock


@fixture
def variables():
    """Provide gazette's flat config via environment variables.

    Only the local-only, non-secret settings are set here (environment, data
    folder, watermark file). The integration tests (content/publishers) need
    real GitHub/Bluesky/Signal credentials and live services -- those are out of
    scope for the local dry-run dev loop and are handled separately.

    Single-mechanism patching: mock.patch.dict alone sets `envs` and clears
    everything else, restoring the original environment on exit. Do not mix in
    monkeypatch.setenv here -- its undo runs after patch.dict's restore and
    deletes the restored variables from the process environment, so every test
    after the first loses the forwarded token.
    """
    share = Path.home() / ".local" / "share"
    envs = {
        # legacy names still asserted by test_environment
        "DYNAMICALSYSTEM_FOLDER": str(share),
        "DYNAMICALSYSTEM_ENVIRONMENT": "pytest",
        # flat gazette config
        "ENVIRONMENT": "pytest",
        "LOG_LEVEL": "DEBUG",
        "DATA_FOLDER": str(share / "dynamicalsystem" / "data"),
        "WATERMARK_FILE": "watermarks.pytests.json",
        # public content URL (not a secret; the token is). Lets the
        # content tests reach GitHub as before.
        "GITHUB_URL": "https://raw.githubusercontent.com/DynamicalSystem/content/main/",
        # GitHub PAT for the private content repo. Forward from the outer
        # environment so tests can access real chart data when available.
        # Captured BEFORE the clearing patch below -- inside it, environ is
        # already empty and the token would always forward as "".
        "GITHUB_TOKEN": environ.get("GITHUB_TOKEN", environ.get("GH_TOKEN", "")),
    }
    with mock.patch.dict(environ, envs, clear=True):
        # settings() is lru_cached and may have been populated at import time
        # (log.py builds the logger eagerly); re-read with the fixture's env.
        from dynamicalsystem.gazette.config import settings

        settings.cache_clear()

        yield  # Restore environment variables

    # Do not leave pytest settings cached for tests that run without this
    # fixture; they re-read from the restored environment.
    settings.cache_clear()
