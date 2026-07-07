"""Loop 06: the web adapter and the publish/serve split.

Pure unit tests -- handlers and the CLI dispatcher are exercised directly, with
no uvicorn, no httpx, no network, no real publish. The live 200 on /health is
verified out-of-band by curling `gazette serve`.
"""
import inspect
from importlib.metadata import version
from os import environ
from unittest import mock


def test_health_handler_ok():
    from dynamicalsystem.gazette.app import health

    body = health()
    assert body["status"] == "ok"
    assert body["version"] == version("dynamicalsystem.gazette")


def test_health_route_registered():
    from dynamicalsystem.gazette.app import app

    assert "/health" in {r.path for r in app.routes}


def test_health_independent_of_env_and_state():
    # cleared env (no DATA_FOLDER / WATERMARK_FILE / tokens): health still answers
    from dynamicalsystem.gazette.app import health

    with mock.patch.dict(environ, clear=True):
        body = health()
    assert body["status"] == "ok"


def test_publish_command_calls_publish_once_not_serve(monkeypatch):
    from dynamicalsystem.gazette import cli as cli_mod
    from dynamicalsystem.gazette import app as app_mod

    called = []
    monkeypatch.setattr(cli_mod, "publish_once", lambda: called.append("publish") or 0)
    monkeypatch.setattr(app_mod, "serve", lambda: called.append("serve") or 0)

    rc = cli_mod.cli(["publish"])

    assert rc == 0
    assert called == ["publish"]  # serve never touched


def test_serve_command_dispatches_to_app_serve(monkeypatch):
    from dynamicalsystem.gazette import cli as cli_mod
    from dynamicalsystem.gazette import app as app_mod

    called = []
    monkeypatch.setattr(app_mod, "serve", lambda: called.append("serve") or 0)

    rc = cli_mod.cli(["serve"])

    assert rc == 0
    assert called == ["serve"]


def test_web_adapter_does_not_trigger_the_sweep():
    # structural independence: serving must not import or call the publish sweep
    from dynamicalsystem.gazette import app as app_mod

    assert "publish_once" not in inspect.getsource(app_mod)
