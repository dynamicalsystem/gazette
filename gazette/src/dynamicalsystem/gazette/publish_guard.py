from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from fcntl import LOCK_EX, LOCK_NB, flock
from json import JSONDecodeError, dump, load
from os import makedirs, replace
from os.path import dirname, join

from dynamicalsystem.gazette.config import settings
from dynamicalsystem.gazette.log import logger


class SweepInProgress(RuntimeError):
    """Another live publish sweep already holds the sweep lock."""

    pass


@contextmanager
def sweep_lock():
    """Serialize live publish sweeps across processes.

    The publish-once guard is check-then-act: two concurrent sweeps could both
    pass ``is_published()`` before either records, and double-post. systemd
    already refuses to start the timer unit twice; this flock extends the same
    guarantee to manual runs alongside the timer. Non-blocking: a second sweep
    raises SweepInProgress and fails fast rather than queueing a stale sweep
    behind the running one.
    """
    config = settings()
    makedirs(config.data_folder, exist_ok=True)
    lock_path = join(config.data_folder, "publish.lock")
    lock_file = open(lock_path, "w")
    try:
        try:
            flock(lock_file, LOCK_EX | LOCK_NB)
        except OSError as e:
            raise SweepInProgress(
                f"Another publish sweep holds {lock_path}; "
                f"refusing to run concurrently."
            ) from e
        yield
    finally:
        # Closing the descriptor releases the flock.
        lock_file.close()


class PublishGuard:
    """Prevent publishing the same (watermark, chart, placing) twice within a
    rolling window.

    Records are stored next to the watermark file as ``published.json``. The
    guard is intentionally simple: it trusts a successful publisher response as
    evidence of delivery and refuses to repeat that exact piece of content to
    the same target until the window has elapsed.
    """

    DEFAULT_WINDOW_HOURS = 24.0

    def __init__(self, window_hours: float = DEFAULT_WINDOW_HOURS) -> None:
        self.config = settings()
        self.window = timedelta(hours=window_hours)
        self.guard_file = join(self.config.data_folder, "published.json")

    def _load(self) -> dict:
        try:
            with open(self.guard_file) as f:
                data = load(f)
        except FileNotFoundError:
            return {}
        except JSONDecodeError as e:
            # A corrupt guard file must not fault the sweep forever; treat it
            # as empty (fail open) and shout so the operator can investigate.
            logger.error(
                f"Corrupt publish guard file {self.guard_file}: {e}. "
                f"Treating as empty; duplicate protection is degraded until "
                f"the next successful publish rewrites it."
            )
            return {}

        if not isinstance(data, dict):
            logger.error(
                f"Publish guard file {self.guard_file} does not contain an "
                f"object; treating as empty."
            )
            return {}

        return data

    def _save(self, data: dict) -> None:
        # Write-temp-then-rename so a crash mid-write cannot corrupt the file.
        folder = dirname(self.guard_file)
        if folder:
            makedirs(folder, exist_ok=True)
        temp_file = self.guard_file + ".tmp"
        with open(temp_file, "w") as f:
            dump(data, f, indent=4)
        replace(temp_file, self.guard_file)

    def _prune(self, data: dict) -> dict:
        """Drop entries older than the window, and any unparseable ones."""
        now = datetime.now(timezone.utc)
        kept = {}
        for key, timestamp_str in data.items():
            try:
                published_at = datetime.fromisoformat(timestamp_str)
            except (TypeError, ValueError):
                logger.warning(f"Dropping invalid publish guard entry: {key}")
                continue
            if now - published_at < self.window:
                kept[key] = timestamp_str
        return kept

    @staticmethod
    def _key(watermark_name: str, chart: str, placing: int) -> str:
        return f"{watermark_name}:{chart}.{placing}"

    def is_published(self, watermark_name: str, chart: str, placing: int) -> bool:
        """Return True if this exact piece has been published within the window."""
        data = self._load()
        timestamp_str = data.get(self._key(watermark_name, chart, placing))
        if not timestamp_str:
            return False

        try:
            published_at = datetime.fromisoformat(timestamp_str)
        except ValueError:
            logger.warning(f"Invalid timestamp in publish guard: {timestamp_str}")
            return False

        if datetime.now(timezone.utc) - published_at < self.window:
            logger.warning(
                f"Skipping {watermark_name} {chart}.{placing}: already published at "
                f"{timestamp_str} (within {self.window.total_seconds() / 3600}h window)."
            )
            return True

        return False

    def record(self, watermark_name: str, chart: str, placing: int) -> None:
        """Record that this exact piece was published now."""
        data = self._prune(self._load())
        data[self._key(watermark_name, chart, placing)] = (
            datetime.now(timezone.utc).isoformat()
        )
        self._save(data)
