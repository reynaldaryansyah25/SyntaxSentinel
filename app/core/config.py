from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "development"
    log_level: str = "INFO"

    gitlab_base_url: str = "https://gitlab.com"
    gitlab_personal_access_token: str = ""
    gitlab_webhook_secret: str = ""
    gitlab_project_id: int | None = None
    gitlab_default_branch: str = "main"

    gcp_project_id: str = ""
    gcp_location: str = "us-central1"
    gemini_model: str = ""

    dry_run: bool = True
    max_trace_chars: int = 4000
    agent_min_confidence: float = 0.75

    @field_validator("gitlab_project_id", mode="before")
    @classmethod
    def empty_project_id_to_none(cls, value: object) -> object:
        if value == "":
            return None
        if isinstance(value, str) and value.startswith(("PASTE_", "your_", "YOUR_")):
            return None
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
