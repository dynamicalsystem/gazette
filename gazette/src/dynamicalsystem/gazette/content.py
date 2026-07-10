from dynamicalsystem.gazette.config import settings
from dynamicalsystem.gazette.utils import url_join
from dynamicalsystem.gazette.log import logger
from requests import get, post

VERDICTS = ("Ignore.", "Buy.", "Explore.")


class ContentProblem(Exception):
    """Base: something about the chart or review stops this target publishing."""


class ChartUnavailable(ContentProblem):
    """The chart file could not be fetched (404, auth, network). A FAULT: it
    hits every target that reads this chart (e.g. an expired PAT)."""


class ChartCorrupt(ContentProblem):
    """The chart fetched but is not valid JSON, or is not a list. A FAULT:
    one bad character (a dropped comma) breaks the whole chart for every
    target. This is the case that must never be mistaken for 'not written yet'."""


class ReviewNotReady(ContentProblem):
    """This placing has no usable review yet -- the index is past the end of
    the chart, or the review/verdict is still blank. Expected and benign:
    hold the watermark quietly and try again next run."""


class ReviewInvalid(ContentProblem):
    """A written review is malformed -- its verdict is not one of VERDICTS.
    A FAULT: the review exists but was fat-fingered, so it will never publish
    until a human fixes it."""


class GitHub:
    def __init__(self, chart, placing):
        self.config = settings()
        self.logger = logger
        self.chart = chart
        self.placing = placing
        self.url = url_join(self.config.github_url, [self.chart + ".json"])

        headers = {
            "Authorization": f"token {self.config.github_token}",
            "Content-Type": "application/json",
        }

        response = get(self.url, headers=headers)

        if not response.ok:
            raise ChartUnavailable(
                f"Chart {chart} unavailable: HTTP {response.status_code} for {response.url}"
            )

        try:
            data = response.json()
        except ValueError as e:  # json.JSONDecodeError is a ValueError subclass
            raise ChartCorrupt(f"Chart {chart} is not valid JSON: {e}") from e

        if not isinstance(data, list):
            raise ChartCorrupt(
                f"Chart {chart} is not a list (got {type(data).__name__})."
            )

        try:
            self.item = data[placing - 1]
        except IndexError as e:
            raise ReviewNotReady(
                f"No review yet for item {placing} in chart {chart}."
            ) from e

    def classify(self) -> str:
        """Grade the fetched item: 'ok', 'not_ready', or 'invalid'.

        'not_ready' (blank/absent review or verdict) is the benign not-written
        state; 'invalid' (a non-empty verdict outside VERDICTS) is a fault.
        """
        keys = ("artist", "work", "review", "verdict")
        item = self.item

        if not isinstance(item, dict) or not all(k in item for k in keys):
            return "not_ready"
        if not all(str(item[k]).strip() for k in keys):
            return "not_ready"
        if item["verdict"] not in VERDICTS:
            return "invalid"
        return "ok"

    def validate_content(self) -> bool:
        return self.classify() == "ok"
