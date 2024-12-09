import abc
from atproto import Client
from re import search
from requests import get, post, ConnectionError
from dynamicalsystem.halogen import config_instance
from dynamicalsystem.halogen import logger
from dynamicalsystem.halogen.utils import cli_hyperlink, possessive, url_join
from dynamicalsystem.gazette.review import Review
from dynamicalsystem.gazette.watermarks import Watermark


def create_publisher(watermark: str):
    w = Watermark(watermark)
    _class = globals()[w.publisher]  # todo: this is a bit of a hack

    return _class(w)


class Publisher(abc.ABC):
    def __init__(self, watermark: Watermark) -> None:
        self.config = config_instance(__name__)
        self.logger = logger
        self.watermark = watermark
        review = Review(chart=watermark.chart, placing=watermark.placing)

        self.chart = review.chart
        self.placing = review.placing

        if d := review.content.validate_content():
            self.content = review
        else:
            self.logger.warning(
                (
                    'Content missing for '
                    f"{cli_hyperlink(review.content.url, {watermark.placing})}"
                )
            )
            return

    @abc.abstractmethod
    def publish(self):
        pass

    @abc.abstractmethod
    def _formatter(self):
        return (
            f"{self.chart}.{self.placing}\n"
            f'{possessive(self.content.artist)} "{self.content.work}"\n'
            f"{self.content.review}\n{self.content.verdict}"
        )


class Bluesky(Publisher):
    def __init__(self, watermark: Watermark) -> None:
        super().__init__(watermark)
        self.client = Client(base_url=self.config.bluesky_url)
        self.client.login(self.config.bluesky_username, self.config.bluesky_password)
        self.logger.debug("__init__")

    def publish(self):
        if (size := len(self._formatter())) > 300:
            self.logger.error(f"Message too long: {size} {self.message}")
            return False

        self._post = self.client.send_post(self._formatter())
        self.logger.debug(self._post.uri)

        return True

    def _formatter(self):
        return super()._formatter()


class Signal(Publisher):
    def __init__(self, watermark: Watermark) -> None:
        super().__init__(watermark)
        self.logger.debug("__init__")

    def publish(self):
        url = url_join(self.config.signal_url, ["v2/send"])
        data = {
            "message": self._formatter(),
            "text_mode": "styled",
            "number": self.config.signal_identity,
            "recipients": [self.watermark.target],
        }
        headers = {"Content-Type": "application/json"}

        try:
            response = post(url, json=data, headers=headers)
        except ConnectionError as e:
            self.logger.error(f"Failed to connect to Signal Messenger: {e}")
            return False

        if not response.ok:
            error = response.json().get("error")
            print("Failed to post to Signal Messenger: %", error.split("\n")[0])
            if response.status_code == 400:
                if search(
                    "The Signal protocol expects that incoming messages are regularly received.",
                    error,
                ):
                    messages = self._messages()
                    self.logger.warning(f"Message count: {len(messages)}")
                    response = post(url, json=data, headers=headers)
                if search("Unregistered user", error):
                    response = True  # todo: not really sure how check if the message actually got sent...

        return response

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

    def _messages(self):
        try:
            url = url_join(
                self.watermark["target"],
                ["v1/receive", self.config.signal_phone_number],
            )
            return len(get(url).json())
        except Exception:
            return False


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
