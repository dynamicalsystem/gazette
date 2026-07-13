import abc
from atproto import Client, client_utils
from grapheme import length as grapheme_length
from re import search
from time import sleep
from requests import get, post, RequestException
from dynamicalsystem.gazette.config import settings
from dynamicalsystem.gazette.log import logger
from dynamicalsystem.gazette.utils import possessive, url_join
from dynamicalsystem.gazette.review import Review
from dynamicalsystem.gazette.watermarks import Watermark
from dynamicalsystem.gazette.content import ReviewInvalid, ReviewNotReady


def create_publisher(watermark: str):
    w = Watermark(watermark)
    if w.placing <= 0:
        # walked off the end of the chart -- benign, hold quietly
        raise ReviewNotReady(f"Chart complete for {watermark} (placing={w.placing})")
    _class = globals()[w.publisher]  # todo: this is a bit of a hack

    return _class(w)


class Publisher(abc.ABC):
    def __init__(self, watermark: Watermark) -> None:
        self.config = settings()
        self.logger = logger
        self.watermark = watermark
        review = Review(chart=watermark.chart, placing=watermark.placing)

        self.chart = review.chart
        self.placing = review.placing

        # Split "not written yet" (benign, hold quietly) from "written wrong"
        # (a fault). Both skip this target without decrementing its watermark.
        status = review.content.classify()
        if status == "ok":
            self.content = review
        elif status == "invalid":
            raise ReviewInvalid(
                f"Review {self.chart}.{self.placing} has an invalid verdict: "
                f"{review.verdict!r}"
            )
        else:
            raise ReviewNotReady(f"Review {self.chart}.{self.placing} not written yet.")

    @abc.abstractmethod
    def publish(self):
        pass

    @abc.abstractmethod
    def _formatter(self):
        return (
            f"{possessive(self.content.artist)}\n"
            f"'{self.content.work}'\n"
            f"{self.content.review}\n"
            f"{self.chart}.{self.placing} - {self.content.verdict}"
        )

class Bluesky(Publisher):
    # Bluesky's app-level post limit is 300 Unicode extended grapheme clusters,
    # not raw bytes or Python code points. The atproto wire model allows 3000
    # chars; the 300-grapheme limit is enforced by the AppView/PDS.
    MAX_POST_GRAPHEMES = 300

    def __init__(self, watermark: Watermark) -> None:
        super().__init__(watermark)

        if (size := grapheme_length(self._formatter())) > self.MAX_POST_GRAPHEMES:
            raise ReviewInvalid(
                f"Review {self.chart}.{self.placing} is {size} graphemes; "
                f"Bluesky limit is {self.MAX_POST_GRAPHEMES}."
            )

        self.client = Client(base_url=self.config.bluesky_url)
        self.client.login(self.config.bluesky_username, self.config.bluesky_password)
        self.logger.debug("__init__")

    def publish(self):
        self._post = self.client.send_post(self._formatter())

        if self.content.verdict == "Buy." and hasattr(self.content, 'url'):
            reply = client_utils.TextBuilder
            reply.link('', self.content.url)
            self._reply = self.client.send_post(text=reply, reply_to=self._post)

        self.logger.debug(self._post.uri)

        return True

    def _formatter(self):
        return super()._formatter()

    def _wip_formatter(self):
        # This prevents people guessing the verdict by the length of the message
        # Needs to be not the last line of the message because Signal trims whitespace
        match self.content.verdict:
            case "Buy.":
                verdict = "||Buy.      ||"
            case "Explore.":
                verdict = "||Explore.||"
            case "Ignore.":
                verdict = "||Ignore.  ||"
            case _:
                verdict = self.content.verdict

        tb = TextBuilder()
        tb.text(possessive(self.content.artist + "\n"))
        tb.text(self.content.work + "\n")
        tb.text(self.content.review + "\n")
        tb.append_spoiler(verdict + "\n")
        tb.text(f"{self.chart}.{self.placing}")

        return (
            f"**{possessive(self.content.artist)}** *'{self.content.work}'*\n"
            f"{self.content.review}\n"
            f"{verdict}\n"
            f"{self.chart}.{self.placing}"
        )

class Signal(Publisher):
    def __init__(self, watermark: Watermark) -> None:
        super().__init__(watermark)
        self.logger.debug("__init__")

    # signal-cli's send can fail transiently (stale websocket ->
    # "Connection terminated unexpectedly"); retry rather than skip the target.
    _RETRY_ATTEMPTS = 3
    _RETRY_BACKOFF = 10  # seconds between transient retries

    def publish(self):
        url = url_join(self.config.signal_url, ["v2/send"])
        data = {
            "message": self._formatter(),
            "text_mode": "styled",
            "number": self.config.signal_identity,
            "recipients": [self.watermark.target],
        }
        headers = {"Content-Type": "application/json"}

        for attempt in range(1, self._RETRY_ATTEMPTS + 1):
            try:
                response = post(url, json=data, headers=headers, timeout=90)
            except RequestException as e:
                self.logger.error(
                    f"Signal send {attempt}/{self._RETRY_ATTEMPTS} -- request error: {e}"
                )
                if attempt < self._RETRY_ATTEMPTS:
                    sleep(self._RETRY_BACKOFF)
                    continue
                return False

            if response.ok:
                return response

            error = response.json().get("error") or ""
            first_line = error.splitlines()[0] if error else str(response.status_code)

            # permanent for this recipient -- do not retry
            if response.status_code == 400 and search("Unregistered user", error):
                return True  # todo: confirm the message actually got sent

            # signal-cli wants its inbox drained before it will send -- drain, retry now
            if response.status_code == 400 and search(
                "incoming messages are regularly received", error
            ):
                count = self._drain_inbox()
                self.logger.warning(f"Drained {count} Signal messages; retrying send")
                continue

            # anything else (incl. the transient SocketException 400) -- back off + retry
            self.logger.error(
                f"Signal send {attempt}/{self._RETRY_ATTEMPTS} failed: {first_line}"
            )
            if attempt < self._RETRY_ATTEMPTS:
                sleep(self._RETRY_BACKOFF)
                continue
            return False

        return False

    def _formatter(self):
        # This prevents people guessing the verdict by the length of the message
        # Needs to be not the last line of the message because Signal trims whitespace
        match self.content.verdict:
            case "Buy.":
                verdict = "||Buy.      ||"
            case "Explore.":
                verdict = "||Explore.||"
            case "Ignore.":
                verdict = "||Ignore.  ||"
            case _:
                verdict = self.content.verdict

        return (
            f"**{possessive(self.content.artist)}** *'{self.content.work}'*\n"
            f"{self.content.review}\n"
            f"{verdict}\n"
            f"{self.chart}.{self.placing}"
        )

    def _drain_inbox(self) -> int:
        """signal-cli requires incoming messages be received periodically, or it
        rejects sends. Drain the receive endpoint so the retried send succeeds.
        """
        try:
            url = url_join(
                self.config.signal_url,
                ["v1/receive", self.config.signal_identity],
            )
            return len(get(url).json())
        except Exception as e:
            self.logger.error(f"Failed to drain Signal inbox: {e}")
            return 0


class Validator(Publisher):
    def __init__(self, watermark: Watermark) -> None:
        super().__init__(watermark)
        self.logger.debug("__init__")

    def _formatter(self):
        return (
            "Validator Publication - "
            f"{self.chart}.{self.placing} - "
            f'{possessive(self.content.artist)} "{self.content.work}". '
            f"{self.content.verdict}"
        )

    def publish(self):
        self.logger.info(self._formatter())

        return True
