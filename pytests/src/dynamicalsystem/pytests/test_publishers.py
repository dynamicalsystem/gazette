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


def test_bluesky_long_message_is_truncated(environment_variables, monkeypatch):
    """A Bluesky post over 300 chars is truncated to 300 chars and published."""
    from atproto import Client
    from types import SimpleNamespace
    from dynamicalsystem.gazette.log import logger
    from dynamicalsystem.gazette.publishers import Bluesky

    monkeypatch.setattr(Client, "login", lambda *args, **kwargs: None)

    sent = []
    monkeypatch.setattr(
        Client, "send_post", lambda self, text: sent.append(text) or SimpleNamespace(uri="at://test")
    )

    publisher = Bluesky.__new__(Bluesky)
    publisher.chart = "tQ26.H"
    publisher.placing = 100
    publisher.logger = logger
    publisher.client = Client()
    publisher.content = SimpleNamespace(verdict="Ignore.")
    publisher._formatter = lambda: "x" * 301

    assert publisher.publish() is True
    assert len(sent) == 1
    assert len(sent[0]) == 300
    assert sent[0].endswith("...")

