"""Download the Gold snapshot (parquet) from the Databricks volume to data/gold/.

The snapshot is written by notebooks/03_embed_gold.py and named after the Delta version of
gold_embeddings it was exported from. The local retriever reads it (no vector database needed
at this size). Prints the file's sha256 so the exact file used by a run can be recorded.

Usage (from repo root):
    python -m scripts.pull_gold              # version from GOLD_VERSION in .env
    python -m scripts.pull_gold --version 1
"""

import argparse
import hashlib
import shutil

import pandas as pd
from databricks.sdk import WorkspaceClient

from src.settings import get_settings


def main() -> None:
    s = get_settings()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--version", type=int, default=s.gold_version, help="Delta version of gold_embeddings")
    version = parser.parse_args().version
    if not (s.databricks_host and s.databricks_token):
        raise SystemExit("Set DATABRICKS_HOST and DATABRICKS_TOKEN in .env")

    remote = f"/Volumes/{s.databricks_catalog}/{s.databricks_schema}/exports/gold_v{version}.parquet"
    local = s.gold_snapshot_path.with_name(f"gold_v{version}.parquet")
    local.parent.mkdir(parents=True, exist_ok=True)

    client = WorkspaceClient(host=s.databricks_host, token=s.databricks_token.get_secret_value())
    with client.files.download(remote).contents as src, open(local, "wb") as dst:
        shutil.copyfileobj(src, dst)

    gold = pd.read_parquet(local)
    assert (gold["gold_delta_version"] == version).all(), "snapshot does not match the requested version"
    sha = hashlib.sha256(local.read_bytes()).hexdigest()
    print(f"{remote} -> {local}")
    print(f"{len(gold)} chunks | {gold['drug'].nunique()} drugs | model {gold['embedding_model'].iloc[0]} "
          f"| silver v{gold['silver_delta_version'].iloc[0]} | run {gold['embed_run_id'].iloc[0]}")
    print(f"sha256 {sha}")


if __name__ == "__main__":
    main()
