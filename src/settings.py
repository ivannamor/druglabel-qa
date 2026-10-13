"""Single source of configuration. Values come from environment variables / `.env`.

Switching LLM provider is one line in `.env`, e.g. LLM_PROVIDER=azure_openai.
Azure OpenAI is the production target; the demo runs on free tiers (see README, "LLM providers").
"""

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProvider = Literal["github_models", "gemini", "azure_openai", "openai", "anthropic"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- LLM for answer generation and KG extraction ---
    llm_provider: LLMProvider = "github_models"
    # Azure: deployment name. GitHub Models: "publisher/model". Others: model name.
    llm_model: str = "openai/gpt-4.1-mini"
    llm_temperature: float = 0.0

    # --- LLM-as-judge: a different model family than the generator reduces self-preference bias ---
    judge_provider: LLMProvider = "gemini"
    judge_model: str = "gemini-2.5-flash"

    # --- Embeddings: a pinned open-source model keeps runs reproducible and free ---
    embedding_provider: Literal["local", "azure_openai", "openai"] = "local"
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    # --- Provider credentials (only the ones in use need a value) ---
    github_token: SecretStr | None = None
    github_models_base_url: str = "https://models.github.ai/inference"
    gemini_api_key: SecretStr | None = None
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
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
