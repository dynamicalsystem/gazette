"""Publish-sweep fault semantics (pure unit tests -- Review, the publishers and
watermarks are mocked, so nothing here touches GitHub, Signal or Bluesky).

The contract:
  - "not written yet" (ReviewNotReady) is held QUIETLY and does not fail the run;
  - a corrupt/unavailable chart, an invalid review, or a failed send is a FAULT:
    it holds the watermark (never advances past a failure), keeps going to the
    other targets, alerts the operator, and makes publish_once() return non-zero.
"""
from types import SimpleNamespace
from pytest import raises


class _FakeContent:
    def __init__(self, status):  # "ok" | "not_ready" | "invalid"
        self._status = status
        self.item = {"artist": "A", "work": "W", "review": "r", "verdict": "Buy."}

    def classify(self):
        return self._status

    def validate_content(self):
        return self._status == "ok"


class _FakeReview:
    def __init__(self, chart, placing, status):
        self.chart = chart
        self.placing = placing
        self.content = _FakeContent(status)
        self.artist = "A"
        self.work = "W"
        self.review = "r"
        self.verdict = "Buy." if status != "invalid" else "Buy"


def _watermark(name="abyss", chart="tQ26.H", placing=100):
    return SimpleNamespace(name=name, chart=chart, placing=placing, target="dev")


def _patch_review(monkeypatch, status):
    from dynamicalsystem.gazette import publishers

    monkeypatch.setattr(
        publishers,
        "Review",
        lambda chart, placing: _FakeReview(chart, placing, status),
    )


def test_valid_content_constructs(monkeypatch):
    from dynamicalsystem.gazette import publishers

    _patch_review(monkeypatch, "ok")
    p = publishers.Validator(_watermark())
    assert p.content.verdict == "Buy."


def test_not_ready_raises_reviewnotready(monkeypatch):
    """An unwritten review makes construction raise ReviewNotReady -- the quiet
    signal publish_once() uses to hold the watermark without failing the run."""
    from dynamicalsystem.gazette import publishers
    from dynamicalsystem.gazette.content import ReviewNotReady

    _patch_review(monkeypatch, "not_ready")
    with raises(ReviewNotReady):
        publishers.Validator(_watermark())


def test_invalid_verdict_raises_reviewinvalid(monkeypatch):
    """A written-but-malformed review (bad verdict) is a fault, distinct from
    'not written yet'."""
    from dynamicalsystem.gazette import publishers
    from dynamicalsystem.gazette.content import ReviewInvalid

    _patch_review(monkeypatch, "invalid")
    with raises(ReviewInvalid):
        publishers.Validator(_watermark())


def _fake_publisher(name, ok):
    """A minimal publisher whose watermark records whether update() ran."""
    p = SimpleNamespace(chart="tQ26.H", placing=100, updated=False)
    p.publish = lambda: ok
    wm = SimpleNamespace(name=name)
    wm.update = lambda: setattr(p, "updated", True)
    p.watermark = wm
    return p


def test_not_ready_is_quiet_and_run_stays_clean(monkeypatch):
    """A not-ready target and a successful target: the run is clean (rc 0), no
    alert, the good target advances, the not-ready one is untouched."""
    import dynamicalsystem.gazette as gazette
    from dynamicalsystem.gazette.content import ReviewNotReady

    good = _fake_publisher("good", ok=True)
    alerts = []

    def fake_create(watermark, live=False):
        if watermark == "notready":
            raise ReviewNotReady("not written yet")
        return {"good": good}[watermark]

    monkeypatch.setattr(gazette, "watermarks", lambda: ["notready", "good"])
    monkeypatch.setattr(gazette, "create_publisher", fake_create)
    monkeypatch.setattr(gazette, "send_alert", lambda msg: alerts.append(msg))

    rc = gazette.publish_once()

    assert rc == 0
    assert good.updated is True
    assert alerts == []  # quiet: not-ready is not a fault


def test_faults_are_loud_hold_and_do_not_abort(monkeypatch):
    """A corrupt chart and a failed send are both faults: the sweep continues to
    the good target (which advances), neither faulted watermark is decremented,
    exactly one alert is sent, and rc is non-zero."""
    import dynamicalsystem.gazette as gazette
    from dynamicalsystem.gazette.content import ChartCorrupt

    failer = _fake_publisher("failer", ok=False)  # send returns False -> fault
    good = _fake_publisher("good", ok=True)
    alerts = []

    def fake_create(watermark, live=False):
        if watermark == "corrupt":
            raise ChartCorrupt("tQ26.H is not valid JSON")
        return {"failer": failer, "good": good}[watermark]

    # corrupt + failed-send come first; a working `good` last proves no abort.
    monkeypatch.setattr(gazette, "watermarks", lambda: ["corrupt", "failer", "good"])
    monkeypatch.setattr(gazette, "create_publisher", fake_create)
    monkeypatch.setattr(gazette, "send_alert", lambda msg: alerts.append(msg))

    rc = gazette.publish_once()

    assert rc == 1                    # loud: the run failed
    assert good.updated is True       # reached and advanced the later target
    assert failer.updated is False    # a failed send did not decrement
    assert len(alerts) == 1           # one summary alert for the whole sweep
    assert "corrupt" in alerts[0] and "failer" in alerts[0]


def test_publish_once_passes_live_to_create_publisher(monkeypatch):
    """publish_once(live=True) forwards live mode to create_publisher."""
    import dynamicalsystem.gazette as gazette

    calls = []

    def fake_create(watermark, live=False):
        calls.append((watermark, live))
        raise gazette.ReviewNotReady("not written yet")

    monkeypatch.setattr(gazette, "watermarks", lambda: ["target"])
    monkeypatch.setattr(gazette, "create_publisher", fake_create)

    gazette.publish_once(live=True)

    assert calls == [("target", True)]


def test_publish_once_default_is_dry_run(monkeypatch):
    """publish_once() defaults to live=False (dry-run)."""
    import dynamicalsystem.gazette as gazette

    calls = []

    def fake_create(watermark, live=False):
        calls.append((watermark, live))
        raise gazette.ReviewNotReady("not written yet")

    monkeypatch.setattr(gazette, "watermarks", lambda: ["target"])
    monkeypatch.setattr(gazette, "create_publisher", fake_create)

    gazette.publish_once()

    assert calls == [("target", False)]
