from dynamicalsystem.halogen.config import config_instance
from dynamicalsystem.halogen import logger
from json import dump, load
from os.path import join


def watermarks():
    config = config_instance(__name__)
    watermark_file = join(config.data_folder, config.watermark_file)

    try:
        with open(watermark_file) as f:
            watermarks = load(f)
    except FileNotFoundError:
        logger.exception(f"{watermark_file} not found.")
        return None

    return watermarks.keys()


class Watermark:
    def __init__(self, name: str) -> None:
        self.name = name
        self.logger = logger
        self.config = config_instance(__name__)
        self.watermark_file = join(self.config.data_folder, self.config.watermark_file)
        self._load()

    def update(self):
        self.placing = self.placing - 1
        try:
            with open(self.watermark_file) as f:
                watermarks = load(f)

            watermarks[self.name]["placing"] = self.placing

            with open(self.watermark_file, "w") as f:
                dump(watermarks, f)

        except FileNotFoundError:
            self.logger.exception(f"{self.watermark_file} not found.")
            return

        except KeyError:
            self.logger.exception(f"Watermark {self.name} not found.")
            return

        self._log_watermark("Updated watermark")

    def _load(self):
        try:
            with open(self.watermark_file) as f:
                watermarks = load(f)
        except FileNotFoundError:
            self.logger.exception(f"{self.watermark_file} not found.")
            return

        try:
            mark = watermarks[self.name]
        except KeyError:
            self.logger.exception(f"Watermark {self.name} not found.")
            return

        self.publisher = mark.get("publisher") or ""
        self.chart = mark.get("chart") or ""
        self.placing = mark.get("placing") or ""
        self.target = mark.get("target") or ""

        self._log_watermark("Loaded watermark")

    def _log_watermark(self, action: str):
        self.logger.info(
            (
                f"{action} -  {self.name} "
                f"{self.publisher} "
                f"{self.chart}."
                f"{self.placing}."
            )
        )
