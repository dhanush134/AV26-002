from functools import lru_cache
from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "LifeTwin AI"
    app_env: str = Field(default="development", alias="APP_ENV")
    database_url: str = Field(alias="DATABASE_URL")
    cors_origins: Annotated[list[str], NoDecode] = Field(default_factory=list, alias="CORS_ORIGINS")
    internal_sync_secret: str | None = Field(default=None, alias="INTERNAL_SYNC_SECRET")
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-5.5", alias="OPENAI_MODEL")
    openai_timeout_seconds: float = Field(default=180, ge=10, le=600, alias="OPENAI_TIMEOUT_SECONDS")
    openai_max_retries: int = Field(default=6, ge=1, le=10, alias="OPENAI_MAX_RETRIES")
    openai_retry_base_seconds: float = Field(default=1.5, ge=0.1, le=30, alias="OPENAI_RETRY_BASE_SECONDS")
    openai_retry_max_seconds: float = Field(default=20, ge=1, le=120, alias="OPENAI_RETRY_MAX_SECONDS")
    openai_validation_retries: int = Field(default=2, ge=1, le=4, alias="OPENAI_VALIDATION_RETRIES")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str] | None) -> list[str]:
        if value is None or value == "":
            return []
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
