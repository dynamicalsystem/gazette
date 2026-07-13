from dynamicalsystem.pytests.environment import variables as environment_variables


def test_bluesky(environment_variables):
    from dynamicalsystem.gazette.publishers import create_publisher

    _ = create_publisher("bluesky")

    assert _.client.me.handle == "dynamicalsystem.com"


def test_signal_init(environment_variables):
    from dynamicalsystem.gazette.publishers import create_publisher

    _ = create_publisher("signal_to_abyss")

    assert _.content.review is not None
    _.publish()


def test_signal_logger(environment_variables):
    from dynamicalsystem.gazette.publishers import create_publisher

    _ = create_publisher("signal_to_abyss")

    _.logger.debug("Test DEBUG log")
    _.logger.info("Test INFO log")
    _.logger.warning("Test WARNING log")
    _.logger.error("Test ERROR log")
    _.logger.critical("Test CRITICAL log")

    try:
        raise AssertionError("Test EXCEPTION log")
    except Exception as e:
        _.logger.exception(e)


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

