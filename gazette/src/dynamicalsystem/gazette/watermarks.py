from datetime import datetime, timezone
from dynamicalsystem.gazette.config import settings
from dynamicalsystem.gazette.log import logger
from json import dump, load
from os.path import join
from shutil import copy2


def watermarks():
    config = settings()
    watermark_file = join(config.data_folder, config.watermark_file)

    try:
        with open(watermark_file) as f:
            watermarks = load(f)
    except FileNotFoundError:
        logger.exception(f"{watermark_file} not found.")
        return None

    return watermarks.keys()


class RouteInvalid(ValueError):
    """A route's `follows` entry is unusable: it names a route that does not
    exist, one on a different chart, itself, or a cycle. A FAULT for that route
    only: it is held and alerted, the other routes still sweep."""


def leader_of(name: str, marks: dict) -> str:
    """Validate `marks[name]['follows']` and return the leader's name, or ""
    when the route follows nothing. `marks` is the loaded watermark file."""
    leader = (marks[name].get("follows") or "").strip()
    if not leader:
        return ""
    if leader not in marks:
        raise RouteInvalid(f"Route {name} follows {leader!r}, which does not exist.")
    if marks[leader].get("chart") != marks[name].get("chart"):
        raise RouteInvalid(
            f"Route {name} follows {leader}, but they are on different charts "
            f"({marks[name].get('chart')!r} vs {marks[leader].get('chart')!r})."
        )
    # walk the chain: a route may not follow itself, directly or indirectly
    seen, cursor = {name}, leader
    while cursor:
        if cursor in seen:
            raise RouteInvalid(f"Route {name} follows a cycle through {cursor}.")
        seen.add(cursor)
        cursor = (marks.get(cursor, {}).get("follows") or "").strip()
    return leader


class Watermark:
    def __init__(self, name: str) -> None:
        self.name = name
        self.logger = logger
        self.config = settings()
        self.watermark_file = join(self.config.data_folder, self.config.watermark_file)
        self._load()

    def update(self):
        self.placing = self.placing - 1
        try:
            with open(self.watermark_file) as f:
                watermarks = load(f)

            old_placing = watermarks[self.name]["placing"]
            watermarks[self.name]["placing"] = self.placing

            # Snapshot before write so a bad manual change is reversible.
            copy2(self.watermark_file, f"{self.watermark_file}.bak")

            with open(self.watermark_file, "w") as f:
                dump(watermarks, f, indent=4)

            # Append an audit entry for every change.
            timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            with open(f"{self.watermark_file}.log", "a") as f:
                f.write(
                    f"{timestamp} "
                    f"watermark={self.name} "
                    f"old={self.chart}.{old_placing} "
                    f"new={self.chart}.{self.placing}\n"
                )

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
        self.placing = mark.get("placing", 0)
        self.target = mark.get("target") or ""
        # optional: the route that must publish a placing before this one may
        self.follows = leader_of(self.name, watermarks)

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
