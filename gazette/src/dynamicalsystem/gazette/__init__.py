from dynamicalsystem.gazette.log import logger
from dynamicalsystem.gazette.publishers import create_publisher
from dynamicalsystem.gazette.watermarks import watermarks
from dynamicalsystem.gazette.content import ContentProblem, ReviewNotReady
from dynamicalsystem.gazette.alerts import send_alert


def publish_once() -> int:
    """Run one publish sweep: for each watermark (target), publish the current
    placing and decrement it on success.

    A target with no written review yet (ReviewNotReady) is held quietly -- that
    fires every run for every unwritten placing and is not a fault. Anything else
    -- a corrupt or unavailable chart, an invalid review, a failed send, or an
    unexpected error -- is a FAULT: it is logged loudly, the watermark is held
    (never advanced past a failure), the sweep continues to the other targets,
    and the function returns non-zero after alerting the operator. This is what
    stops a silent, all-target outage from ever looking like a clean run again.

    Library entry point -- called by the `publish` CLI and the systemd timer.
    Does not touch the web stack.
    """
    marks = watermarks()
    if not marks:
        logger.warning("No watermarks to publish (missing or empty watermark file).")
        return 0

    faults = []
    for watermark in marks:
        try:
            publisher = create_publisher(watermark=watermark)
            if publisher.publish():
                logger.info(
                    f"Published - {publisher.chart}.{publisher.placing} "
                    f"on {publisher.__class__.__name__} "
                    f"with {publisher.watermark.name}."
                )
                publisher.watermark.update()
            else:
                logger.error(
                    f"Publish failed - {publisher.chart}.{publisher.placing} "
                    f"on {publisher.__class__.__name__} "
                    f"with {publisher.watermark.name}."
                )
                faults.append(
                    f"{watermark}: send failed for "
                    f"{publisher.chart}.{publisher.placing}"
                )
        except ReviewNotReady as e:
            # benign: the review is not written yet -- hold and try next run
            logger.info(f"{e} Watermark {watermark} -- not ready, held.")
            continue
        except ContentProblem as e:
            # corrupt / unavailable chart, or an invalid review -- a real fault
            logger.error(f"{e} Watermark {watermark} -- FAULT, held.")
            faults.append(f"{watermark}: {e}")
            continue
        except Exception as e:
            # never let one odd target silently abort the whole sweep
            logger.exception(f"Unexpected error on watermark {watermark} -- FAULT, held.")
            faults.append(f"{watermark}: unexpected {type(e).__name__}: {e}")
            continue

    if faults:
        summary = (
            f"gazette publish: {len(faults)} fault(s) held, nothing advanced "
            f"for them:\n" + "\n".join(f"- {f}" for f in faults)
        )
        logger.error(summary)
        send_alert(summary)
        return 1

    return 0
