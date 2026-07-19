from dynamicalsystem.gazette.log import logger
from dynamicalsystem.gazette.publishers import create_publisher
from dynamicalsystem.gazette.publish_guard import PublishGuard
from dynamicalsystem.gazette.watermarks import Watermark, watermarks
from dynamicalsystem.gazette.content import ContentProblem, ReviewNotReady
from dynamicalsystem.gazette.alerts import send_alert


def publish_once(live: bool = False) -> int:
    """Run one publish sweep: for each watermark (target), publish the current
    placing and decrement it on success.

    Args:
        live: If False (default), every target is run through the Validator
            publisher -- a dry-run that logs what would be published. If True,
            real publishers are used, but only if `GAZETTE_LIVE=1` is also set
            in the environment.

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

    guard = PublishGuard()
    faults = []
    for watermark in marks:
        try:
            # Check the publish-once guard before doing anything expensive
            # (e.g., logging into Bluesky). This prevents double posts from
            # retries, timer misfires, or manual re-runs.
            preview = Watermark(watermark)
            preview_chart = getattr(preview, "chart", None) or ""
            preview_placing = getattr(preview, "placing", None) or 0
            if preview_chart and guard.is_published(
                watermark, preview_chart, preview_placing
            ):
                logger.warning(
                    f"Skipping {watermark}: {preview_chart}.{preview_placing} "
                    f"was already published within the guard window."
                )
                continue

            publisher = create_publisher(watermark=watermark, live=live)
            if publisher.publish():
                logger.info(
                    f"Published - {publisher.chart}.{publisher.placing} "
                    f"on {publisher.__class__.__name__} "
                    f"with {publisher.watermark.name}."
                )
                if live:
                    guard.record(watermark, publisher.chart, publisher.placing)
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
