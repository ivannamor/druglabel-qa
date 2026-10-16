"""Download a parquet snapshot exported by a Databricks notebook from the volume to data/.

Snapshots are named after the Delta version of the table they were exported from:
- gold:           notebooks/03_embed_gold.py     -> exports/gold_v{n}.parquet           -> data/gold/
- label_metadata: notebooks/04_label_metadata.py -> exports/label_metadata_v{n}.parquet -> data/metadata/
The local code reads them (no vector database or SQL warehouse needed at this size). Prints the file's
sha256 so the exact file used by a run can be recorded.

Usage (from repo root):
    python -m scripts.pull_export gold                 # version from GOLD_VERSION in .env
    python -m scripts.pull_export label_metadata --version 0
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
    parser.add_argument("name", choices=["gold", "label_metadata"])
    parser.add_argument("--version", type=int, help="Delta version of the table (default: from .env)")
    args = parser.parse_args()
    if not (s.databricks_host and s.databricks_token):
        raise SystemExit("Set DATABRICKS_HOST and DATABRICKS_TOKEN in .env")

    default_version, default_path = {
        "gold": (s.gold_version, s.gold_snapshot_path),
        "label_metadata": (s.label_metadata_version, s.label_metadata_path),
    }[args.name]
    version = default_version if args.version is None else args.version
    remote = f"/Volumes/{s.databricks_catalog}/{s.databricks_schema}/exports/{args.name}_v{version}.parquet"
    local = default_path.with_name(f"{args.name}_v{version}.parquet")
    local.parent.mkdir(parents=True, exist_ok=True)

    client = WorkspaceClient(host=s.databricks_host, token=s.databricks_token.get_secret_value())
    with client.files.download(remote).contents as src, open(local, "wb") as dst:
        shutil.copyfileobj(src, dst)

    df = pd.read_parquet(local)
    assert (df[f"{args.name}_delta_version"] == version).all(), "snapshot does not match the requested version"
    print(f"{remote} -> {local}")
    print(f"{len(df)} rows | {df['drug'].nunique()} drugs")
    print(f"sha256 {hashlib.sha256(local.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
