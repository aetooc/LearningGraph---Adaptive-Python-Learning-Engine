from dataclasses import dataclass
from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


@dataclass(frozen=True)
class LLMProviderConfig:
    name: str
    api_key: SecretStr | None
    model: str | None
    base_url: str
    api_key_setting: str
    model_setting: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", extra="ignore")

    database_url: str = "postgresql+psycopg://learning:learning@localhost:5433/learning"
    llm_provider: Literal["openai", "groq"] = "openai"
    openai_api_key: SecretStr | None = None
    openai_model: str | None = None
    openai_base_url: str = "https://api.openai.com/v1"
    groq_api_key: SecretStr | None = None
    groq_model: str | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    mastery_threshold: float = Field(default=0.70, gt=0, le=1)
    cors_origins: list[str] = Field(default_factory=list) # holds frontend addresses

    @property
    def llm(self) -> LLMProviderConfig:
        provider = self.llm_provider
        prefix = provider.upper()
        return LLMProviderConfig(
            name={"openai": "OpenAI", "groq": "Groq"}[provider],
            api_key=getattr(self, f"{provider}_api_key"),
            model=getattr(self, f"{provider}_model"),
            base_url=getattr(self, f"{provider}_base_url"),
            api_key_setting=f"{prefix}_API_KEY",
            model_setting=f"{prefix}_MODEL",
        )

    @field_validator("database_url")
    @classmethod
    def select_installed_postgres_driver(cls, value: str) -> str:
        # Hosted databases provide generic URLs; this project installs psycopg 3.
        for scheme in ("postgres://", "postgresql://"):
            if value.startswith(scheme):
                return "postgresql+psycopg://" + value[len(scheme):]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
