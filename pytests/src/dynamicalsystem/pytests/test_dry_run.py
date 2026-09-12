"""A dry-run changes nothing in the data folder (pure unit tests).

The contract:
  - publish_once() (dry-run) never calls watermark.update(), even when the
    Validator reports success; it logs what it would have advanced;
  - publish_once(live=True) still advances on success;
  - a route whose CONFIGURED publisher is Validator (a dev/validation route)
    advances in live mode: the gate is the mode, not the publisher class.
"""
from types import SimpleNamespace


def _fake_publisher(name, ok=True):
    p = SimpleNamespace(chart="tQ26.H", placing=33, updated=False)
    p.publish = lambda: ok
    wm = SimpleNamespace(name=name)
    wm.update = lambda: setattr(p, "updated", True)
    p.watermark = wm
    return p


def _run(monkeypatch, pub, live, messages=None):
    """Run one sweep over a single route. `messages` (a list) collects INFO
    lines; the real logger does not propagate, so caplog cannot see it."""
    from contextlib import nullcontext
    import dynamicalsystem.gazette as gazette

    if messages is not None:
        quiet = lambda *a, **k: None
        monkeypatch.setattr(
            gazette,
            "logger",
            SimpleNamespace(
                info=lambda m: messages.append(m),
                warning=quiet, error=quiet, exception=quiet,
            ),
        )
    monkeypatch.setattr(gazette, "sweep_lock", nullcontext)
    monkeypatch.setattr(gazette, "watermarks", lambda: ["target"])
    monkeypatch.setattr(gazette, "create_publisher", lambda watermark, live=False: pub)
    monkeypatch.setattr(gazette, "send_alert", lambda msg: None)
    monkeypatch.setattr(
        gazette,
        "PublishGuard",
        lambda: SimpleNamespace(is_published=lambda *a: False, record=lambda *a: None),
    )
    return gazette.publish_once(live=live)


def test_dry_run_does_not_advance_watermark(monkeypatch):
    pub = _fake_publisher("target")
    messages = []
    rc = _run(monkeypatch, pub, live=False, messages=messages)
    assert rc == 0
    assert pub.updated is False
    assert any("would advance target past tQ26.H.33" in m for m in messages)


def test_live_run_advances_watermark(monkeypatch):
    pub = _fake_publisher("target")
    rc = _run(monkeypatch, pub, live=True)
    assert rc == 0
    assert pub.updated is True


def test_validator_route_advances_in_live_mode(monkeypatch):
    """The real Validator class, on a route configured to use it, advances when
    the sweep is live: the mode gates the update, not the publisher type."""
    from dynamicalsystem.gazette import publishers

    class _Content:
        item = {"artist": "A", "work": "W", "review": "r", "verdict": "Buy."}

        def classify(self):
            return "ok"

    monkeypatch.setattr(
        publishers,
        "Review",
        lambda chart, placing: SimpleNamespace(
            chart=chart, placing=placing, content=_Content(),
            artist="A", work="W", review="r", verdict="Buy.",
        ),
    )
    wm = SimpleNamespace(name="dev", chart="tQ26.H", placing=33, target="dev", updated=False)
    wm.update = lambda: setattr(wm, "updated", True)
    pub = publishers.Validator(wm)
    rc = _run(monkeypatch, pub, live=True)
    assert rc == 0
    assert wm.updated is True


def test_dry_run_with_validator_route_does_not_advance(monkeypatch):
    from dynamicalsystem.gazette import publishers

    class _Content:
        item = {"artist": "A", "work": "W", "review": "r", "verdict": "Buy."}

        def classify(self):
            return "ok"

    monkeypatch.setattr(
        publishers,
        "Review",
        lambda chart, placing: SimpleNamespace(
            chart=chart, placing=placing, content=_Content(),
            artist="A", work="W", review="r", verdict="Buy.",
        ),
    )
    wm = SimpleNamespace(name="dev", chart="tQ26.H", placing=33, target="dev", updated=False)
    wm.update = lambda: setattr(wm, "updated", True)
    pub = publishers.Validator(wm)
    rc = _run(monkeypatch, pub, live=False)
    assert rc == 0
    assert wm.updated is False
