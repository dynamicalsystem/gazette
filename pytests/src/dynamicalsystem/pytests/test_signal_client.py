"""Loop 02 verification: the Signal publisher's HTTP contract.

Pure unit tests with requests mocked -- they never hit a live Signal service,
so they are safe to run anywhere (no real /v2/send).
"""
import logging
from types import SimpleNamespace


def _make_signal():
    """A Signal publisher with the network-heavy __init__ bypassed."""
    from dynamicalsystem.gazette.publishers import Signal

    s = Signal.__new__(Signal)
    s.config = SimpleNamespace(
        signal_url="http://signal:8080", signal_identity="+100"
    )
    s.logger = logging.getLogger("test.signal")
    s.watermark = SimpleNamespace(target="group.ABYSS")
    s.content = SimpleNamespace(
        artist="Boards of Canada", work="Geogaddi", review="ok", verdict="Buy."
    )
    s.chart = "tQ"
    s.placing = 5
    return s


def _response(ok=True, status=201, error=None):
    return SimpleNamespace(
        ok=ok, status_code=status, json=lambda: {"error": error} if error else {}
    )


def test_signal_publish_posts_expected_contract(monkeypatch):
    from dynamicalsystem.gazette import publishers

    calls = []

    def fake_post(url, json, headers):
        calls.append((url, json, headers))
        return _response(ok=True, status=201)

    monkeypatch.setattr(publishers, "post", fake_post)

    s = _make_signal()
    s.publish()

    assert len(calls) == 1
    url, body, _ = calls[0]
    assert url == "http://signal:8080/v2/send"
    assert body["number"] == "+100"
    assert body["recipients"] == ["group.ABYSS"]
    assert body["text_mode"] == "styled"
    # verdict is spoiler-wrapped, not on the last line
    assert "||Buy." in body["message"]
    assert body["message"].splitlines()[-1] == "tQ.5"


def test_signal_publish_drains_and_retries_on_400(monkeypatch):
    from dynamicalsystem.gazette import publishers

    posts = []
    error = "The Signal protocol expects that incoming messages are regularly received."

    def fake_post(url, json, headers):
        posts.append(url)
        # first attempt fails with the "regularly received" 400, retry succeeds
        if len(posts) == 1:
            return _response(ok=False, status=400, error=error)
        return _response(ok=True, status=201)

    drained = []

    def fake_get(url):
        drained.append(url)
        return SimpleNamespace(json=lambda: [{"msg": 1}, {"msg": 2}])

    monkeypatch.setattr(publishers, "post", fake_post)
    monkeypatch.setattr(publishers, "get", fake_get)

    s = _make_signal()
    s.publish()

    assert len(posts) == 2  # original + retry
    assert drained == ["http://signal:8080/v1/receive/+100"]
