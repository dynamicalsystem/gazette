from os import environ
from pathlib import Path
from pytest import fixture
from unittest import mock


@fixture
def variables(monkeypatch):
    """Provide gazette's flat config via environment variables.

    Only the local-only, non-secret settings are set here (environment, data
    folder, watermark file). The integration tests (content/publishers) need
    real GitHub/Bluesky/Signal credentials and live services -- those are out of
    scope for the local dry-run dev loop and are handled separately.
    """
    share = Path.home() / ".local" / "share"
    with mock.patch.dict(environ, clear=True):
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
        }
        for k, v in envs.items():
            monkeypatch.setenv(k, v)

        # settings() is lru_cached and may have been populated at import time
        # (log.py builds the logger eagerly); re-read with the fixture's env.
        from dynamicalsystem.gazette.config import settings

        settings.cache_clear()

        yield  # Restore environment variables
