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

    # state
    data_folder: str = ""
    watermark_file: str = "watermarks.json"


@lru_cache(maxsize=1)
def settings() -> Settings:
    return Settings()
