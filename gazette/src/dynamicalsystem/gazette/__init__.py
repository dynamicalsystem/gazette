from dynamicalsystem.halogen import logger
from dynamicalsystem.gazette.publishers import create_publisher
from dynamicalsystem.gazette.watermarks import watermarks


def main() -> int:
    _ = watermarks()

    for watermark in _:
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
        except ValueError as e:  # no review found
            logger.exception((f"{str(e)} Watermark {watermark}."))
            continue

    return 0
