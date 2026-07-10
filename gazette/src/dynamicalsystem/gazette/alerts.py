"""Operational alerting for the publish sweep.

Deliberately self-contained: a fault alert must NOT build a Publisher, because
constructing one fetches a review -- which can fail for the very reason we are
alerting about. So this posts to the Signal service directly.
"""
from requests import post, RequestException

from dynamicalsystem.gazette.config import settings
from dynamicalsystem.gazette.log import logger
from dynamicalsystem.gazette.utils import url_join


def send_alert(message: str) -> bool:
    """Push one operational alert to the ops Signal recipient. Best-effort:
    returns True if delivered, False (with a logged reason) otherwise.
    """
    config = settings()
    target = config.signal_ops_target
    if not target:
        logger.error("signal_ops_target unset -- alert not delivered: %s", message)
        return False

    try:
        response = post(
            url_join(config.signal_url, ["v2/send"]),
            json={
                "message": message,
                "number": config.signal_identity,
                "recipients": [target],
            },
            headers={"Content-Type": "application/json"},
            timeout=30,
        )
    except RequestException as e:
        logger.error("Alert send failed: %s", e)
        return False

    if not response.ok:
        logger.error("Alert send rejected: HTTP %s", response.status_code)
        return False

    return True
