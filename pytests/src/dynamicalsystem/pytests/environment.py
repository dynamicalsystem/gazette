from os import environ
from pathlib import Path
from pytest import fixture
from unittest import mock


@fixture
def variables(monkeypatch):
    with mock.patch.dict(environ, clear=True):
        envs = {
            "DYNAMICALSYSTEM_FOLDER": str(Path.home() / ".local" / "share"),
            "DYNAMICALSYSTEM_ENVIRONMENT": "pytest",
        }
        for k, v in envs.items():
            monkeypatch.setenv(k, v)

        yield  # Restore environment variables
