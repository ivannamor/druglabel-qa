"""Single source of configuration. Values come from environment variables / `.env`.

Switching LLM provider is one line in `.env`: LLM_PROVIDER=azure_openai | openai | anthropic.
"""

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- LLM ---
    llm_provider: Literal["azure_openai", "openai", "anthropic"] = "azure_openai"
    # For Azure these are *deployment names*; for OpenAI/Anthropic, model names.
    llm_model: str = "gpt-4.1-mini"
    embedding_model: str = "text-embedding-3-small"
    llm_temperature: float = 0.0

    azure_openai_endpoint: str | None = None
    azure_openai_api_key: SecretStr | None = None
    azure_openai_api_version: str = "2024-10-21"
    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None

    # --- Data ---
    openfda_api_key: SecretStr | None = None  # optional; raises the daily request limit

    # --- Retrieval ---
    retrieval_mode: Literal["vector", "graph", "hybrid"] = "vector"
    top_k: int = 5


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
