"""A publish/content failure must skip to the next target WITHOUT advancing
the failed target's watermark.

Pure unit tests: Review and the publisher/watermark machinery are mocked, so
nothing here touches GitHub, Signal or Bluesky.
"""
from types import SimpleNamespace
from pytest import raises


class _FakeContent:
    def __init__(self, valid):
        self._valid = valid
        self.url = "https://example.test/tQ26.H.json"

    def validate_content(self):
        return self._valid


class _FakeReview:
    """Stand-in for review.Review with controllable validity."""

    def __init__(self, chart, placing, valid):
        self.chart = chart
        self.placing = placing
        self.content = _FakeContent(valid)
        self.artist = "Artist" if valid else ""
        self.work = "Work" if valid else ""
        self.review = "review" if valid else ""
        self.verdict = "Buy." if valid else ""


def _watermark(name="abyss", chart="tQ26.H", placing=100):
    return SimpleNamespace(name=name, chart=chart, placing=placing, target="dev")


def test_invalid_content_raises_valueerror(monkeypatch):
    """The fix: an unwritten review makes publisher construction raise
    ValueError (the signal main() uses to skip without updating)."""
    from dynamicalsystem.gazette import publishers

    monkeypatch.setattr(
        publishers,
        "Review",
        lambda chart, placing: _FakeReview(chart, placing, valid=False),
    )

    with raises(ValueError):
        publishers.Validator(_watermark())


def test_valid_content_constructs(monkeypatch):
    """Guard: valid content still constructs a publisher and keeps the review."""
    from dynamicalsystem.gazette import publishers

    monkeypatch.setattr(
        publishers,
        "Review",
        lambda chart, placing: _FakeReview(chart, placing, valid=True),
    )

    p = publishers.Validator(_watermark())
    assert p.content.verdict == "Buy."


def _fake_publisher(name, ok):
    """A minimal publisher whose watermark records whether update() ran."""
    p = SimpleNamespace(chart="tQ26.H", placing=100, updated=False)
    p.publish = lambda: ok
    wm = SimpleNamespace(name=name)
    wm.update = lambda: setattr(p, "updated", True)
    p.watermark = wm
    return p


def test_main_continues_past_failures_without_updating(monkeypatch):
    """The invariant: a content failure (raise) and a publish failure (False)
    are both skipped, the loop reaches later targets, and neither failed
    target's watermark is decremented."""
    import dynamicalsystem.gazette as gazette

    failer = _fake_publisher("failer", ok=False)
    good = _fake_publisher("good", ok=True)

    def fake_create(watermark):
        if watermark == "empty":
            raise ValueError("Content missing for tQ26.H.100")
        return {"failer": failer, "good": good}[watermark]

    # order matters: the failures come first, so a working `good` at the end
    # proves the loop was not aborted by them.
    monkeypatch.setattr(gazette, "watermarks", lambda: ["empty", "failer", "good"])
    monkeypatch.setattr(gazette, "create_publisher", fake_create)

    rc = gazette.publish_once()

    assert rc == 0                    # no crash
    assert good.updated is True       # loop reached the later target and advanced it
    assert failer.updated is False    # publish()->False did not decrement
    # the "empty" target raised before any watermark existed -> nothing to update
