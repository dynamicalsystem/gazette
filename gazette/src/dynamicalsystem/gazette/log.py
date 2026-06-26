import logging
from sys import stdout

from dynamicalsystem.gazette.config import settings


def _build_logger() -> logging.Logger:
    """Stdout-only logger. The platform (docker/systemd) captures it.

    Replaces halogen's logger, including its SignalHandler that posted WARNING+
    log records to a live Signal service -- that coupling is intentionally gone.
    """
    logger = logging.getLogger("dynamicalsystem.gazette")
    if logger.handlers:
        return logger

    handler = logging.StreamHandler(stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)
    logger.setLevel(settings().log_level)
    logger.propagate = False

    return logger


logger = _build_logger()
