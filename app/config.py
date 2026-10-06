from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    database_url: str = "postgresql+psycopg://learning:learning@localhost:5433/learning"
    llm_provider: Literal["openai", "groq"] = "openai"
    openai_api_key: SecretStr | None = None
    openai_model: str | None = None
    groq_api_key: SecretStr | None = None
    groq_model: str | None = None
    mastery_threshold: float = Field(default=0.70, gt=0, le=1)


@lru_cache
def get_settings() -> Settings:
    return Settings()
