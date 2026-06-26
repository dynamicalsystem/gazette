"""Loop 01 verification: the flat config module replaces halogen.

These are pure unit tests -- no network, no live services -- unlike the
integration tests in this suite.
"""
from os import environ
import sys
from unittest import mock


def test_settings_reads_flat_env():
    from dynamicalsystem.gazette.config import Settings

    env = {
        "GITHUB_URL": "https://example/raw/",
        "GITHUB_TOKEN": "tok",
        "BLUESKY_USERNAME": "user",
        "SIGNAL_URL": "http://signal:8010",
        "SIGNAL_IDENTITY": "+100",
        "DATA_FOLDER": "/data",
        "WATERMARK_FILE": "w.json",
        "ENVIRONMENT": "pytest",
        "LOG_LEVEL": "DEBUG",
    }
    with mock.patch.dict(environ, env, clear=True):
        s = Settings(_env_file=None)

    assert s.github_url == "https://example/raw/"
    assert s.github_token == "tok"
    assert s.signal_url == "http://signal:8010"
    assert s.signal_identity == "+100"
    assert s.data_folder == "/data"
    assert s.watermark_file == "w.json"
    assert s.environment == "pytest"
    assert s.log_level == "DEBUG"


def test_settings_defaults():
    from dynamicalsystem.gazette.config import Settings

    with mock.patch.dict(environ, {}, clear=True):
        s = Settings(_env_file=None)

    assert s.environment == "dev"
    assert s.bluesky_url == "https://bsky.social"
    assert s.watermark_file == "watermarks.json"


def test_gazette_imports_without_halogen():
    """gazette must not depend on dynamicalsystem.halogen at import time."""
    for name in [m for m in sys.modules if m.startswith("dynamicalsystem.gazette")]:
        del sys.modules[name]

    # Make any `import dynamicalsystem.halogen` raise, proving gazette is clean.
    with mock.patch.dict(sys.modules, {"dynamicalsystem.halogen": None}):
        import dynamicalsystem.gazette  # noqa: F401
        import dynamicalsystem.gazette.config  # noqa: F401
        import dynamicalsystem.gazette.log  # noqa: F401
        import dynamicalsystem.gazette.content  # noqa: F401
        import dynamicalsystem.gazette.publishers  # noqa: F401
        import dynamicalsystem.gazette.watermarks  # noqa: F401
        import dynamicalsystem.gazette.utils  # noqa: F401
