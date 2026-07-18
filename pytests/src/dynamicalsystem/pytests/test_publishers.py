from dynamicalsystem.pytests.environment import variables as environment_variables


def test_bluesky(environment_variables, monkeypatch):
    from dynamicalsystem.gazette.publishers import create_publisher

    monkeypatch.setenv("GAZETTE_LIVE", "1")
    _ = create_publisher("example_bluesky_route", live=True)

    assert _.client.me.handle == "dynamicalsystem.com"


def test_signal_init(environment_variables, monkeypatch):
    from dynamicalsystem.gazette.publishers import create_publisher

    monkeypatch.setenv("GAZETTE_LIVE", "1")
    _ = create_publisher("example_signal_route", live=True)

    assert _.content.review is not None
    _.publish()


def test_signal_logger(environment_variables, monkeypatch):
    from dynamicalsystem.gazette.publishers import create_publisher

    monkeypatch.setenv("GAZETTE_LIVE", "1")
    _ = create_publisher("example_signal_route", live=True)

    _.logger.debug("Test DEBUG log")
    _.logger.info("Test INFO log")
    _.logger.warning("Test WARNING log")
    _.logger.error("Test ERROR log")
    _.logger.critical("Test CRITICAL log")

    try:
        raise AssertionError("Test EXCEPTION log")
    except Exception as e:
        _.logger.exception(e)


class _FakeContent:
    def __init__(self):
        self.item = {"artist": "A", "work": "W", "review": "r", "verdict": "Buy."}

    def classify(self):
        return "ok"


class _FakeReview:
    def __init__(self, chart, placing):
        self.chart = chart
        self.placing = placing
        self.content = _FakeContent()
        self.artist = "A"
        self.work = "W"
        self.review = "r"
        self.verdict = "Buy."


def _patch_review(monkeypatch):
    from dynamicalsystem.gazette import publishers

    monkeypatch.setattr(
        publishers,
        "Review",
        lambda chart, placing: _FakeReview(chart, placing),
    )


def test_create_publisher_defaults_to_validator(environment_variables, monkeypatch):
    """Without live=True, create_publisher always returns Validator."""
    from dynamicalsystem.gazette.publishers import Validator, create_publisher

    _patch_review(monkeypatch)
    _ = create_publisher("example_signal_route")

    assert isinstance(_, Validator)


def test_live_publisher_requires_env_guard(environment_variables, monkeypatch):
    """A live publisher request without GAZETTE_LIVE=1 raises LiveModeRequired."""
    from pytest import raises
    from dynamicalsystem.gazette.publishers import LiveModeRequired, create_publisher

    _patch_review(monkeypatch)
    monkeypatch.delenv("GAZETTE_LIVE", raising=False)

    with raises(LiveModeRequired):
        create_publisher("example_signal_route", live=True)


def test_bluesky_long_message_raises_review_invalid(environment_variables, monkeypatch):
    """A Bluesky post over 300 graphemes is rejected as invalid content."""
    from pytest import raises
    from types import SimpleNamespace
    from dynamicalsystem.gazette import publishers
    from dynamicalsystem.gazette.content import ReviewInvalid

    class _LongReview:
        def __init__(self, chart, placing):
            self.chart = chart
            self.placing = placing
            self.content = self
            self.artist = "A"
            self.work = "W"
            self.review = "x" * 400
            self.verdict = "Buy."

        def classify(self):
            return "ok"

    monkeypatch.setattr(
        publishers, "Review", lambda chart, placing: _LongReview(chart, placing)
    )

    with raises(ReviewInvalid):
        publishers.Bluesky(
            SimpleNamespace(name="bluesky", chart="tQ26.H", placing=100)
        )

