from dynamicalsystem.gazette.log import logger
from dynamicalsystem.gazette.publishers import create_publisher
from dynamicalsystem.gazette.watermarks import watermarks


def publish_once() -> int:
    """Run one publish sweep: for each watermark (target), publish the current
    placing and decrement it on success. Skips targets with no usable review and
    holds their watermark. Library entry point -- called by the `publish` CLI and
    (via loop 07) by the systemd timer. Does not touch the web stack.
    """
    marks = watermarks()
    if not marks:
        logger.warning("No watermarks to publish (missing or empty watermark file).")
        return 0

    for watermark in marks:
        try:
            publisher = create_publisher(watermark=watermark)
            if publisher.publish():
                logger.info(
                    (
                        f"Published - {publisher.chart}.{publisher.placing} "
                        f"on {str(publisher.__class__.__name__)} "
                        f"with {publisher.watermark.name}."
                    )
                )
                publisher.watermark.update()
            else:
                logger.error(
                    (
                        f"Publish failed - {publisher.chart}.{publisher.placing} "
                        f"on {str(publisher.__class__.__name__)} "
                        f"with {publisher.watermark.name}."
                    )
                )
        except ValueError as e:  # no review yet / chart complete -- expected
            # Not a fault: skip this target and hold its watermark. A traceback
            # here would fire every scheduled run for every unwritten placing.
            logger.warning(f"{e} Watermark {watermark} -- skipping, watermark held.")
            continue

    return 0
