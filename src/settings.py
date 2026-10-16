"""Single source of configuration. Values come from environment variables / `.env`.

Switching LLM provider is one line in `.env`, e.g. LLM_PROVIDER=azure_openai.
Azure OpenAI is the production target; the demo runs on Google AI Studio's free tier
(see README, "LLM providers").
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

LLMProvider = Literal["gemini", "azure_openai", "openai", "anthropic"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- LLM for answer generation and KG extraction ---
    llm_provider: LLMProvider = "gemini"
    llm_model: str = "gemini-3.1-flash-lite"  # Azure: deployment name; others: model name
    llm_fallback_model: str | None = None  # optional; mixing models in one evaluation makes configs incomparable
    llm_temperature: float = 0.0
    answer_prompt: str = "answer_v1"  # file in prompts/, versioned by name

    # --- LLM-as-judge: should be at least as capable as the generator ---
    judge_provider: LLMProvider = "gemini"
    judge_model: str = "gemini-3.5-flash-lite"
    judge_fallback_model: str | None = None  # optional; must not be the generator model

    # --- Embeddings: a pinned open-source model keeps runs reproducible and free ---
    embedding_provider: Literal["local", "azure_openai", "openai"] = "local"
    embedding_model: str = "BAAI/bge-small-en-v1.5"

    # --- Provider credentials (only the ones in use need a value) ---
    gemini_api_key: SecretStr | None = None
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    azure_openai_endpoint: str | None = None
    azure_openai_api_key: SecretStr | None = None
    azure_openai_api_version: str = "2024-10-21"
    openai_api_key: SecretStr | None = None
    anthropic_api_key: SecretStr | None = None

    # --- Data ---
    openfda_api_key: SecretStr | None = None  # optional; raises the daily request limit

    # --- Databricks (Gold snapshot download, MLflow tracking) ---
    databricks_host: str | None = None  # https://<workspace>.cloud.databricks.com
    databricks_token: SecretStr | None = None  # personal access token
    databricks_catalog: str = "workspace"
    databricks_schema: str = "druglabel_qa"
    gold_version: int = 0  # Delta version of gold_embeddings whose snapshot the retriever uses
    mlflow_experiment: str | None = None  # default: /Users/<your Databricks user>/druglabel-qa

    @property
    def gold_snapshot_path(self) -> Path:
        """Local copy of the Gold snapshot, downloaded by scripts/pull_gold.py."""
        return Path(f"data/gold/gold_v{self.gold_version}.parquet")

    # --- Retrieval ---
    retrieval_mode: Literal["vector", "graph", "hybrid"] = "vector"
    top_k: int = 5
    dedup_threshold: float = 0.95  # same drug + same section + cosine >= this = one passage (see src/retrieval/vector.py)


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide settings instance."""
    return Settings()
