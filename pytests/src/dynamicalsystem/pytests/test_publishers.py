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


def test_get_watermarks(environment_variables):
    from dynamicalsystem.gazette.watermarks import watermarks

    _ = watermarks()
    assert "signal_to_abyss" in _
    assert "bluesky" in _
