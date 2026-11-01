"""Environment-backed application settings."""

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import model_validator


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "academic-services-platform-api"
    app_env: Literal["development", "testing", "staging", "production"] = (
        "development"
    )
    debug: bool = False
    secret_key: SecretStr | None = None
    database_url: str | None = None
    redis_url: str | None = None
    telegram_bot_token: SecretStr | None = None
    telegram_webhook_secret: SecretStr | None = None
    telegram_auth_max_age_seconds: int = 300
    file_storage_dir: str = ".local/private_uploads"
    file_upload_max_bytes: int = 10 * 1024 * 1024

    @model_validator(mode="after")
    def validate_production_settings(self) -> "Settings":
        if self.telegram_auth_max_age_seconds < 60:
            raise ValueError("telegram_auth_max_age_seconds must be at least 60.")
        if self.file_upload_max_bytes < 1:
            raise ValueError("file_upload_max_bytes must be positive.")
        if self.app_env == "production":
            if not self.database_url:
                raise ValueError("DATABASE_URL is required in production.")
            if not self.secret_key or len(
                self.secret_key.get_secret_value()
            ) < 32:
                raise ValueError(
                    "SECRET_KEY must contain at least 32 characters in production."
                )
            if self.debug:
                raise ValueError("DEBUG must be disabled in production.")
        return self


@lru_cache
def get_settings() -> Settings:
    """Return the cached process-wide settings instance."""
    return Settings()