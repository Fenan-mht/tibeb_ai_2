"""Application settings and provider configuration loader.

Loads environment variables from .env and task provider selections from YAML.
Enforces security constraints (e.g., refuses AUTH_MODE=none in production).
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class ProviderSpec(BaseModel):
    provider: str
    model: str | None = None
    voice: str | None = None
    path: str | None = None
    mode: str | None = None


class ChatConfig(BaseModel):
    tutor: ProviderSpec
    flashcards: ProviderSpec


class ConfigFile(BaseModel):
    chat: ChatConfig
    embedder: ProviderSpec
    stt: ProviderSpec
    tts: ProviderSpec
    storage: ProviderSpec
    payments: ProviderSpec


class Settings(BaseSettings):
    """Core application settings merged from environment variables and config YAML."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_ENV: Literal["development", "test", "production"] = "test"
    AUTH_MODE: Literal["none", "sms"] = "none"
    CONFIG_PATH: str = "config/test.yaml"

    # Database & Cache
    DATABASE_URL: str = Field(default="postgresql://postgres:postgres@localhost:5432/postgres")
    TEST_DATABASE_URL: str = Field(default="postgresql://postgres:postgres@localhost:5435/test_db")
    REDIS_URL: str = Field(default="redis://localhost:6379/0")

    # Provider Secrets
    GROQ_API_KEY: str | None = None
    GOOGLE_APPLICATION_CREDENTIALS: str | None = None
    CHAPA_SECRET_KEY: str | None = None
    CHAPA_WEBHOOK_SECRET: str | None = None
    JWT_SECRET: str = "default_secret_key_change_in_production"

    # Loaded YAML configuration
    providers: ConfigFile | None = None

    @model_validator(mode="after")
    def validate_security_and_load_yaml(self) -> "Settings":
        # Security invariant: Rule from architecture & playbook
        if self.APP_ENV == "production" and self.AUTH_MODE == "none":
            raise ValueError(
                "Refusing to start: AUTH_MODE cannot be 'none' when APP_ENV is 'production'"
            )

        # Load YAML provider configuration if not explicitly provided
        if self.providers is None:
            config_file_path = Path(self.CONFIG_PATH)
            if not config_file_path.is_absolute():
                # Check relative to working directory or api root
                api_root = Path(__file__).parent.parent
                candidate = api_root / self.CONFIG_PATH
                if candidate.exists():
                    config_file_path = candidate

            if config_file_path.exists():
                with open(config_file_path, "r", encoding="utf-8") as f:
                    raw_yaml = yaml.safe_load(f) or {}
                self.providers = ConfigFile.model_validate(raw_yaml)
            else:
                # Default fallback config if YAML not found (e.g. unit tests without filesystem access)
                self.providers = ConfigFile(
                    chat=ChatConfig(
                        tutor=ProviderSpec(provider="groq", model="openai/gpt-oss-120b"),
                        flashcards=ProviderSpec(provider="groq", model="openai/gpt-oss-20b"),
                    ),
                    embedder=ProviderSpec(provider="local", model="BAAI/bge-m3"),
                    stt=ProviderSpec(provider="none"),
                    tts=ProviderSpec(provider="google", voice="am-ET-Wavenet-B"),
                    storage=ProviderSpec(provider="local", path="./data/files"),
                    payments=ProviderSpec(provider="chapa", mode="test"),
                )

        return self


@lru_cache
def get_settings() -> Settings:
    """Helper to instantiate cached application settings."""
    return Settings()

