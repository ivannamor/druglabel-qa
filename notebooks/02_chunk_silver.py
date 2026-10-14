# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Chunk label sections → `silver_chunks`
# MAGIC
# MAGIC Reads `bronze_labels` **at a pinned Delta version**, keeps the clinically relevant sections,
# MAGIC cleans them and splits them into chunks. One row per chunk, with
# MAGIC `chunk_id = {label_id}:{section}:{n}` — the ID every answer will cite.
# MAGIC
# MAGIC Chunking: first by numbered subsection ("5.1 …", modern labels only), then long pieces are split
# MAGIC at sentence boundaries into windows of at most `MAX_CHARS`.
# MAGIC
# MAGIC Traceability columns on every row: `bronze_delta_version`, `bronze_ingest_run_id`, `chunk_run_id`,
# MAGIC `chunked_at`, `chunker_params` and `git_commit`. The table is overwritten on each run; earlier
# MAGIC runs stay available through Delta time travel.

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("schema", "druglabel_qa")
dbutils.widgets.text("bronze_version", "", "bronze_labels version (empty = latest)")
dbutils.widgets.text("git_commit", "", "git commit of the repo")

CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")
BRONZE_VERSION = dbutils.widgets.get("bronze_version").strip()
GIT_COMMIT = dbutils.widgets.get("git_commit").strip() or "unknown"
BRONZE = f"{CATALOG}.{SCHEMA}.bronze_labels"
TABLE = f"{CATALOG}.{SCHEMA}.silver_chunks"

# COMMAND ----------

# MAGIC %md ## 1 · Read Bronze at a pinned version

# COMMAND ----------

if not BRONZE_VERSION:
    BRONZE_VERSION = str(spark.sql(f"DESCRIBE HISTORY {BRONZE} LIMIT 1").collect()[0]["version"])

bronze = spark.sql(f"""
    SELECT label_id, set_id, version, effective_time, drug, atc_code, role, raw_json, ingest_run_id
    FROM {BRONZE} VERSION AS OF {int(BRONZE_VERSION)}
""").toPandas()
print(f"{len(bronze)} labels from {BRONZE} version {BRONZE_VERSION}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2 · Chunking rules
# MAGIC
# MAGIC Pure Python, no Spark: this cell can be tested outside Databricks.

# COMMAND ----------

import re

MAX_CHARS = 1200  # ~300 tokens: well inside the 512-token limit of small open-source embedding models
OVERLAP_CHARS = 150  # whole trailing sentences, up to this length, are repeated in the next chunk

# Sections kept, in label order, and the group used for reporting and filtering.
# Old-format labels (before the 2006 Physician Labeling Rule) have WARNINGS/PRECAUTIONS
# instead of WARNINGS AND PRECAUTIONS.
SECTION_GROUPS = {
    "boxed_warning": "warnings",
    "indications_and_usage": "indications",
    "dosage_and_administration": "dosage",
    "dosage_forms_and_strengths": "dosage",
    "contraindications": "contraindications",
    "warnings_and_cautions": "warnings",
    "warnings": "warnings",
    "precautions": "warnings",
    "adverse_reactions": "adverse_reactions",
    "drug_interactions": "interactions",
    "use_in_specific_populations": "specific_populations",
    "pregnancy": "specific_populations",
    "nursing_mothers": "specific_populations",
    "pediatric_use": "specific_populations",
    "geriatric_use": "specific_populations",
    "overdosage": "overdosage",
    "description": "product",
    "clinical_pharmacology": "pharmacology",
    "mechanism_of_action": "pharmacology",
    "pharmacodynamics": "pharmacology",
    "pharmacokinetics": "pharmacology",
    "how_supplied": "product",
    "storage_and_handling": "product",
}
# Not used (see README "Label sections used"): clinical_studies, patient-facing text
# (spl_medguide, information_for_patients), nonclinical toxicology, package label, recent changes.

# openFDA also exposes subsections as their own fields (e.g. `pregnancy` repeats 8.1 of
# USE IN SPECIFIC POPULATIONS). When the parent is present we keep only the parent: no duplicate
# chunks, and in old labels these child fields are sometimes filled with the wrong subsection.
PARENTS = {
    "pregnancy": ("use_in_specific_populations", "precautions"),
    "nursing_mothers": ("use_in_specific_populations", "precautions"),
    "pediatric_use": ("use_in_specific_populations", "precautions"),
    "geriatric_use": ("use_in_specific_populations", "precautions"),
    "drug_interactions": ("precautions",),  # old format: Drug Interactions is a subsection of PRECAUTIONS
    "mechanism_of_action": ("clinical_pharmacology",),
    "pharmacodynamics": ("clinical_pharmacology",),
    "pharmacokinetics": ("clinical_pharmacology",),
    "storage_and_handling": ("how_supplied",),
}

# Section titles that differ from the field name.
TITLES = {
    "warnings_and_cautions": r"warnings\s+(?:and|&)\s+precautions",
    "how_supplied": r"how\s+supplied(?:\s*/\s*storage\s+(?:and|&)\s+handling)?",
}

SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z(\[])")


def strip_header(section: str, text: str) -> tuple[str | None, str]:
    """Remove the leading section title (e.g. '5 WARNINGS AND PRECAUTIONS'); return (section number, body)."""
    title = TITLES.get(section) or r"\s+".join(r"(?:and|&)" if w == "and" else w for w in section.split("_"))
    header = re.compile(r"^(?:(\d{1,2})(?:\.\d{1,2})?\s+)?" + title + r"\b\s*:?\s*", re.I)
    m = header.match(text)
    return (m.group(1), text[m.end():]) if m else (None, text)


def split_subsections(body: str, number: str) -> list[tuple[str | None, str]]:
    """Split at numbered subsection titles of this section ('5.1 Increased Risk…').

    Cross-references like '(5.2)' are not split points: a title follows whitespace and starts
    with a capital letter. The text before the first subsection (the summary) gets None.
    """
    pieces = re.split(rf"\s(?={number}\.\d{{1,2}}\s+[A-Z])", body)
    out = []
    for piece in pieces:
        m = re.match(rf"({number}\.\d{{1,2}})\s", piece)
        out.append((m.group(1) if m else None, piece))
    return out


def split_long(text: str) -> list[str]:
    """Split text longer than MAX_CHARS at sentence boundaries, with a small sentence overlap."""
    if len(text) <= MAX_CHARS:
        return [text]
    sentences = []
    for s in SENTENCE_END.split(text):
        # a sentence longer than MAX_CHARS (e.g. a flattened table) is cut hard
        sentences += [s[i:i + MAX_CHARS] for i in range(0, len(s), MAX_CHARS)]
    chunks, current = [], []
    for s in sentences:
        if current and len(" ".join(current + [s])) > MAX_CHARS:
            chunks.append(" ".join(current))
            tail = []
            for prev in reversed(current):
                if len(" ".join([prev] + tail)) > OVERLAP_CHARS:
                    break
                tail.insert(0, prev)
            current = tail if len(" ".join(tail + [s])) <= MAX_CHARS else []
        current.append(s)
    chunks.append(" ".join(current))
    return chunks


def chunk_label(label: dict) -> list[dict]:
    """All chunks of one openFDA label (parsed JSON), in label order."""
    out = []
    for section, group in SECTION_GROUPS.items():
        if section not in label or any(p in label for p in PARENTS.get(section, ())):
            continue
        text = re.sub(r"\s+", " ", " ".join(label[section])).strip()
        number, body = strip_header(section, text)
        pieces = split_subsections(body, number) if number else [(None, body)]
        n = 0
        for subsection, piece in pieces:
            for chunk in split_long(piece.strip()):
                if not chunk:
                    continue
                n += 1
                out.append({
                    "chunk_id": f"{label['id']}:{section}:{n}",
                    "section": section,
                    "section_group": group,
                    "subsection": subsection,
                    "chunk_index": n,
                    "text": chunk,
                })
    return out

# COMMAND ----------

# MAGIC %md ## 3 · Chunk all labels

# COMMAND ----------

import json

rows = []
for b in bronze.itertuples():
    label = json.loads(b.raw_json)
    for chunk in chunk_label(label):
        rows.append({
            **chunk,
            "label_id": b.label_id,
            "set_id": b.set_id,
            "label_version": b.version,
            "effective_time": b.effective_time,
            "label_format": "PLR" if "warnings_and_cautions" in label else "old",
            "drug": b.drug,
            "brand_names": "; ".join(label.get("openfda", {}).get("brand_name", [])),
            "atc_code": b.atc_code,
            "role": b.role,
            "n_chars": len(chunk["text"]),
            "bronze_ingest_run_id": b.ingest_run_id,
        })
print(f"{len(rows)} chunks from {len(bronze)} labels")

# COMMAND ----------

# MAGIC %md ## 4 · Quality checks

# COMMAND ----------

import pandas as pd

chunks = pd.DataFrame(rows)

dupes = chunks["chunk_id"].duplicated().sum()
assert dupes == 0, f"{dupes} duplicate chunk_ids"
assert (chunks["n_chars"] > 0).all(), "empty chunks"
assert chunks["n_chars"].max() <= MAX_CHARS, "chunk longer than MAX_CHARS"
missing = set(bronze["label_id"]) - set(chunks["label_id"])
assert not missing, f"{len(missing)} labels produced no chunks: {sorted(missing)[:5]}"

# Not errors, but worth knowing: labels without a section the assistant relies on.
for group in ["indications", "contraindications", "interactions"]:
    without = set(bronze["label_id"]) - set(chunks.loc[chunks["section_group"] == group, "label_id"])
    print(f"labels without {group:<18}: {len(without)}")

# COMMAND ----------

# MAGIC %md ## 5 · Write `silver_chunks` and record the Delta version

# COMMAND ----------

import uuid
from datetime import datetime, timezone

from pyspark.sql import functions as F

run_id = str(uuid.uuid4())
params = json.dumps({"max_chars": MAX_CHARS, "overlap_chars": OVERLAP_CHARS, "sections": list(SECTION_GROUPS)})

df = (spark.createDataFrame(chunks)
      .withColumn("bronze_table", F.lit(BRONZE))
      .withColumn("bronze_delta_version", F.lit(int(BRONZE_VERSION)))
      .withColumn("chunk_run_id", F.lit(run_id))
      .withColumn("chunked_at", F.lit(datetime.now(timezone.utc)))
      .withColumn("chunker_params", F.lit(params))
      .withColumn("git_commit", F.lit(GIT_COMMIT)))

df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(TABLE)

version = spark.sql(f"DESCRIBE HISTORY {TABLE} LIMIT 1").collect()[0]["version"]
print(f"Wrote {df.count()} rows to {TABLE} | Delta version {version} | from bronze v{BRONZE_VERSION} | run {run_id}")

# COMMAND ----------

display(spark.table(TABLE)
        .groupBy("section_group")
        .agg(F.count("*").alias("chunks"), F.countDistinct("label_id").alias("labels"),
             F.round(F.avg("n_chars")).alias("avg_chars"))
        .orderBy("section_group"))

# COMMAND ----------

display(spark.table(TABLE).groupBy("label_format").agg(F.countDistinct("label_id").alias("labels")))

# COMMAND ----------

# Spot check: the chunks of one label's WARNINGS AND PRECAUTIONS
example = spark.table(TABLE).filter("drug = 'apixaban' AND section = 'warnings_and_cautions'").select("label_id").first()
if example:
    display(spark.table(TABLE)
            .filter(F.col("label_id") == example["label_id"])
            .filter("section = 'warnings_and_cautions'")
            .select("chunk_id", "subsection", "n_chars", "text")
            .orderBy("chunk_index"))
