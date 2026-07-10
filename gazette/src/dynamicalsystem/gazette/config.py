from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Flat gazette configuration.

    Values are read from environment variables (case-insensitive) and, for local
    development, from a `.env` file. On the cloud the same names are injected as
    real environment variables (OCI Vault). This replaces the halogen config
    library and its per-module env-name prefixes.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: str = "dev"
    log_level: str = "INFO"

    # content (GitHub raw JSON)
    github_url: str = ""
    github_token: str = ""

    # bluesky publisher
    bluesky_url: str = "https://bsky.social"
    bluesky_username: str = ""
    bluesky_password: str = ""

    # signal publisher (external Signal service over HTTP)
    signal_url: str = ""
    signal_identity: str = ""

    # operational alerts: a Signal recipient (number or group id) that gets a
    # message when a publish sweep holds any fault. Unset -> no alert is sent
    # (the sweep still exits non-zero). Optional so dev/dry-run stays silent.
    signal_ops_target: str = ""

    # state
    data_folder: str = ""
    watermark_file: str = "watermarks.json"

    # web service (gazette serve)
    http_host: str = "0.0.0.0"
    http_port: int = 8000


@lru_cache(maxsize=1)
def settings() -> Settings:
    return Settings()
