# Databricks notebook source
# MAGIC %md
# MAGIC # 03 · Embed chunks → `gold_embeddings`
# MAGIC
# MAGIC Reads `silver_chunks` **at a pinned Delta version** and computes one embedding per chunk with a pinned
# MAGIC open-source model (`BAAI/bge-small-en-v1.5`, ONNX build run by `fastembed`; the same library and model
# MAGIC embed the questions at query time, locally).
# MAGIC
# MAGIC Each chunk is embedded with a short context header (`drug (brand) · section · subsection`), so a passage
# MAGIC that never names the drug can still be found. The header is stored in `embed_text`; `text` stays the
# MAGIC citable label text.
# MAGIC
# MAGIC Outputs: the Delta table `gold_embeddings` and a parquet snapshot `exports/gold_v{version}.parquet` in the
# MAGIC volume, which the local retrieval code downloads (`scripts/pull_export.py gold`).
# MAGIC
# MAGIC Traceability columns on every row: `silver_delta_version`, `embed_run_id`, `embedded_at`,
# MAGIC `embedding_model`, `embedding_source`, `fastembed_version` and `git_commit`.

# COMMAND ----------

# MAGIC %pip install fastembed==0.9.0

# COMMAND ----------

dbutils.library.restartPython()

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("schema", "druglabel_qa")
dbutils.widgets.text("silver_version", "", "silver_chunks version (empty = latest)")
dbutils.widgets.text("git_commit", "", "git commit of the repo")

CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")
SILVER_VERSION = dbutils.widgets.get("silver_version").strip()
GIT_COMMIT = dbutils.widgets.get("git_commit").strip() or "unknown"
SILVER = f"{CATALOG}.{SCHEMA}.silver_chunks"
TABLE = f"{CATALOG}.{SCHEMA}.gold_embeddings"
EXPORT_DIR = f"/Volumes/{CATALOG}/{SCHEMA}/exports"

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"

# COMMAND ----------

# MAGIC %md ## 1 · Read Silver at a pinned version

# COMMAND ----------

if not SILVER_VERSION:
    SILVER_VERSION = str(spark.sql(f"DESCRIBE HISTORY {SILVER} LIMIT 1").collect()[0]["version"])

chunks = spark.sql(f"""
    SELECT chunk_id, label_id, set_id, label_version, effective_time, label_format, drug, brand_names,
           atc_code, role, section, section_group, subsection, chunk_index, text
    FROM {SILVER} VERSION AS OF {int(SILVER_VERSION)}
""").toPandas()
print(f"{len(chunks)} chunks from {SILVER} version {SILVER_VERSION}")

# COMMAND ----------

# MAGIC %md ## 2 · Build the text to embed

# COMMAND ----------

import hashlib
import re


def context_header(row) -> str:
    """'apixaban (Eliquis) · warnings and cautions · 5.2' — brand omitted when it is just the generic name."""
    brand_names = row.brand_names if isinstance(row.brand_names, str) else ""  # null may arrive as None or NaN
    brands = [b for b in brand_names.split("; ") if b and b.lower() != row.drug.lower()]
    drug = f"{row.drug} ({', '.join(brands)})" if brands else row.drug
    parts = [drug, row.section.replace("_", " ")] + ([row.subsection] if isinstance(row.subsection, str) else [])
    return " · ".join(parts)


def text_hash(text: str) -> str:
    """Fingerprint of the normalized text: equal hashes = identical passage (e.g. copied across generic labels)."""
    return hashlib.sha256(re.sub(r"\s+", " ", text).strip().lower().encode()).hexdigest()


chunks["embed_text"] = [f"{context_header(r)}\n{r.text}" for r in chunks.itertuples()]
chunks["text_hash"] = chunks["text"].map(text_hash)
print(chunks["embed_text"].iloc[0][:300])

# COMMAND ----------

# MAGIC %md ## 3 · Embed

# COMMAND ----------

import time
from importlib.metadata import version as pkg_version

import numpy as np
from fastembed import TextEmbedding

model = TextEmbedding(EMBEDDING_MODEL)
EMBEDDING_SOURCE = next(m["sources"]["hf"] for m in TextEmbedding.list_supported_models()
                        if m["model"] == EMBEDDING_MODEL)  # exact Hugging Face repo of the ONNX build
FASTEMBED_VERSION = pkg_version("fastembed")

texts = chunks["embed_text"].tolist()

# Measure speed on a first batch and print an estimate, so a slow run can be stopped early.
start = time.time()
first = list(model.embed(texts[:200], batch_size=64))
rate = len(first) / (time.time() - start)
print(f"{rate:.1f} chunks/s → estimated {len(texts) / rate / 60:.0f} min for {len(texts)} chunks", flush=True)

rest = list(model.embed(texts[200:], batch_size=64))
vectors = np.array(first + rest, dtype=np.float32)
print(f"{len(vectors)} embeddings, dim {vectors.shape[1]}, {time.time() - start:.0f}s "
      f"| {EMBEDDING_SOURCE} | fastembed {FASTEMBED_VERSION}")

# COMMAND ----------

# MAGIC %md ## 4 · Quality checks

# COMMAND ----------

assert len(vectors) == len(chunks), "one embedding per chunk"
assert vectors.shape[1] == 384, f"unexpected dimension {vectors.shape[1]}"
assert np.isfinite(vectors).all(), "NaN or infinite values"
norms = np.linalg.norm(vectors, axis=1)
assert np.allclose(norms, 1, atol=1e-3), "embeddings are expected to be normalized (cosine = dot product)"

dup_groups = chunks.groupby("text_hash").size()
print(f"{chunks['text_hash'].nunique()} distinct passages in {len(chunks)} chunks "
      f"({(dup_groups > 1).sum()} passages appear more than once, mostly copies across generic labels)")

# COMMAND ----------

# MAGIC %md ## 5 · Write `gold_embeddings` and the parquet snapshot

# COMMAND ----------

import uuid
from datetime import datetime, timezone

from pyspark.sql import functions as F

run_id = str(uuid.uuid4())
gold = chunks.assign(
    embedding=[v.tolist() for v in vectors],
    embedding_model=EMBEDDING_MODEL,
    embedding_source=EMBEDDING_SOURCE,
    fastembed_version=FASTEMBED_VERSION,
    silver_table=SILVER,
    silver_delta_version=int(SILVER_VERSION),
    embed_run_id=run_id,
    embedded_at=datetime.now(timezone.utc),
    git_commit=GIT_COMMIT,
)

spark.createDataFrame(gold).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(TABLE)
version = spark.sql(f"DESCRIBE HISTORY {TABLE} LIMIT 1").collect()[0]["version"]

print(f"Wrote {len(gold)} rows to {TABLE} | Delta version {version} | from silver v{SILVER_VERSION} | run {run_id}")

# COMMAND ----------

# MAGIC %md
# MAGIC Snapshot for the local retriever: read back from the table version just written, so the file is an exact
# MAGIC copy of it. After running the widgets cell, this cell can also be run on its own to re-export the latest version.

# COMMAND ----------

import numpy as np

GOLD_VERSION = spark.sql(f"DESCRIBE HISTORY {TABLE} LIMIT 1").collect()[0]["version"]
snapshot = spark.sql(f"SELECT * FROM {TABLE} VERSION AS OF {GOLD_VERSION}").toPandas()
snapshot.attrs.clear()  # toPandas() attaches Spark query metrics here; pandas cannot write them to parquet
snapshot["embedding"] = [np.asarray(v, dtype=np.float32) for v in snapshot["embedding"]]
snapshot["gold_delta_version"] = GOLD_VERSION

spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.exports")
export_path = f"{EXPORT_DIR}/gold_v{GOLD_VERSION}.parquet"
snapshot.to_parquet(export_path, index=False)
print(f"Snapshot: {export_path} ({len(snapshot)} rows, Delta version {GOLD_VERSION})")

# COMMAND ----------

# Spot check: nearest chunks to one question, computed the way the local retriever will do it.
question = "What are the contraindications of apixaban?"
q = np.array(list(model.query_embed([question])), dtype=np.float32)[0]
top = np.argsort(-(vectors @ q))[:5]
display(chunks.iloc[top][["chunk_id", "drug", "section", "subsection", "text"]].assign(score=(vectors @ q)[top]))
