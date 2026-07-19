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

    def fake_post(url, json, headers, **kwargs):
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

    def fake_post(url, json, headers, **kwargs):
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


def test_signal_publish_retries_transient_socket_error(monkeypatch):
    """A transient signal-cli SocketException (400) is retried, not skipped."""
    from dynamicalsystem.gazette import publishers

    monkeypatch.setattr(publishers, "sleep", lambda *_: None)  # no real backoff
    error = "Failed to send message: Connection terminated unexpectedly (SocketException)"
    posts = []

    def fake_post(url, json, headers, **kwargs):
        posts.append(url)
        if len(posts) == 1:
            return _response(ok=False, status=400, error=error)  # transient
        return _response(ok=True, status=201)

    monkeypatch.setattr(publishers, "post", fake_post)

    s = _make_signal()
    result = s.publish()

    assert len(posts) == 2  # failed once, retried, succeeded
    assert result.ok is True


def test_signal_publish_gives_up_after_all_attempts(monkeypatch):
    """Persistent failure exhausts the attempts and returns False (watermark held)."""
    from dynamicalsystem.gazette import publishers

    monkeypatch.setattr(publishers, "sleep", lambda *_: None)
    error = "Failed to send message: Connection terminated unexpectedly (SocketException)"
    posts = []

    def fake_post(url, json, headers, **kwargs):
        posts.append(url)
        return _response(ok=False, status=400, error=error)

    monkeypatch.setattr(publishers, "post", fake_post)

    s = _make_signal()
    result = s.publish()

    assert result is False
    assert len(posts) == s._RETRY_ATTEMPTS  # tried the full budget


def test_signal_publish_does_not_retry_mismatched_devices(monkeypatch):
    """MismatchedDevicesException (409) is non-retriable to avoid duplicate posts."""
    from dynamicalsystem.gazette import publishers

    monkeypatch.setattr(publishers, "sleep", lambda *_: None)
    error = (
        "Failed to send message: java.io.IOException: "
        "org.whispersystems.signalservice.internal.push.exceptions."
        "MismatchedDevicesException: StatusCode: 409 (IOException) "
        "(UnexpectedErrorException)"
    )
    posts = []

    def fake_post(url, json, headers, **kwargs):
        posts.append(url)
        return _response(ok=False, status=400, error=error)

    monkeypatch.setattr(publishers, "post", fake_post)

    s = _make_signal()
    result = s.publish()

    assert result is False
    assert len(posts) == 1  # no retry
