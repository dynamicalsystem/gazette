from dynamicalsystem.halogen.config import config_instance
from dynamicalsystem.halogen.utils import url_join
from dynamicalsystem.halogen import logger
from requests import get, post

class GitHub:
    def __init__(self, chart, placing):
        self.config = config_instance(__name__)
        self.logger = logger
        self.chart = chart
        self.placing = placing
        self.url = url_join(
            self.config.github_url,
            [self.chart + ".json"]
        )[:-1] # TDOO: Remove trailing slash in halogen.utils.url_join

        headers = {
            "Authorization": f"token {self.config.github_token}",
            "Content-Type": "application/json",
        }

        response = get(self.url, headers=headers)

        if response.ok:
            try:
                item = response.json()[placing-1]
            except (ValueError) as e:
                message = f"Bad things for item {placing} in series {chart}."
                raise ValueError(message) from e
            except (IndexError, ValueError) as e:
                message = f"No review found for item {placing} in series {chart}."
                raise IndexError(message) from e

            self.item = item
        else:
            self.item = None        

    def validate_content(self):
        keys = ["artist", "work", "review", "verdict"]
        verdicts = ["Ignore.", "Buy.", "Explore."]

        # Keys exist
        if not all(key in self.item for key in keys):
            return False

        # Values are not empty strings
        if not all(bool(self.item.get(key)) for key in keys):
            return False

        # Verdict is one of the formattable options
        if not self.item["verdict"] in verdicts:
            return False

        return True
