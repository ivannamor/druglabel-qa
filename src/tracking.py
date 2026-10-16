"""MLflow tracking on Databricks: connection, git state, and the parameters every run must record.

A run is reproducible from: git commit + prompt (name and sha256) + data versions (Gold snapshot,
Silver) + config. Uncommitted changes break that, so they are tagged (`git_dirty`) and flagged.
"""

import os
import subprocess
from functools import lru_cache

import mlflow
from databricks.sdk import WorkspaceClient

from src.retrieval.vector import get_retriever
from src.settings import get_settings


@lru_cache
def init_tracking() -> str:
    """Point MLflow at the Databricks workspace in settings; return the experiment path."""
    s = get_settings()
    os.environ["DATABRICKS_HOST"] = s.databricks_host
    os.environ["DATABRICKS_TOKEN"] = s.databricks_token.get_secret_value()
    mlflow.set_tracking_uri("databricks")
    experiment = s.mlflow_experiment or f"/Users/{WorkspaceClient().current_user.me().user_name}/druglabel-qa/druglabel-qa-runs"
    mlflow.set_experiment(experiment)
    return experiment


def git_state() -> tuple[str, bool]:
    """(HEAD commit, whether tracked files have uncommitted changes)."""
    def git(*args: str) -> str:
        return subprocess.run(["git", *args], capture_output=True, text=True, check=True).stdout.strip()
    return git("rev-parse", "HEAD"), bool(git("status", "--porcelain", "--untracked-files=no"))


def config_params() -> dict[str, str | int | float]:
    """Model, retrieval and data parameters of the current configuration."""
    s, r = get_settings(), get_retriever()
    return {
        "llm_provider": s.llm_provider,
        "llm_model": s.llm_model,
        "llm_temperature": s.llm_temperature,
        "retrieval_mode": s.retrieval_mode,
        "top_k": s.top_k,
        "dedup_threshold": s.dedup_threshold,
        "graph_max_passages": s.graph_max_passages,
        "label_metadata_version": s.label_metadata_version,
        "embedding_model": s.embedding_model,
        "gold_delta_version": r.gold_version,
        "gold_snapshot_sha256": r.snapshot_sha256,
        "silver_delta_version": r.silver_version,
    }
