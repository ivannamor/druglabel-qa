# Databricks notebook source
# MAGIC %md
# MAGIC # 04 · Label metadata → `label_metadata`
# MAGIC
# MAGIC One row per label with product attributes from openFDA's `openfda` block in `bronze_labels`
# MAGIC (pinned Delta version): route of administration, product type, brand names, manufacturer and
# MAGIC application number (`NDA…` = brand or 505(b)(2) product, `ANDA…` = generic).
# MAGIC
# MAGIC Why: one drug can have labels for different products with different indications (dipyridamole
# MAGIC tablets are an antiplatelet; dipyridamole injection is a diagnostic agent for cardiac imaging).
# MAGIC Downstream steps join on `label_id` to tell them apart; the chunks and embeddings do not change.
# MAGIC
# MAGIC Outputs: the Delta table `label_metadata` and the snapshot `exports/label_metadata_v{version}.parquet`.

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
TABLE = f"{CATALOG}.{SCHEMA}.label_metadata"
EXPORT_DIR = f"/Volumes/{CATALOG}/{SCHEMA}/exports"

# COMMAND ----------

# MAGIC %md ## 1 · Read Bronze at a pinned version and extract the product attributes

# COMMAND ----------

import json

import pandas as pd

if not BRONZE_VERSION:
    BRONZE_VERSION = str(spark.sql(f"DESCRIBE HISTORY {BRONZE} LIMIT 1").collect()[0]["version"])

bronze = spark.sql(f"""
    SELECT label_id, set_id, version, effective_time, drug, raw_json
    FROM {BRONZE} VERSION AS OF {int(BRONZE_VERSION)}
""").collect()


def joined(values: list[str] | None) -> str | None:
    """Sorted, de-duplicated values joined with '; ' (openFDA fields are lists)."""
    return "; ".join(sorted({v.strip() for v in values or [] if v and v.strip()})) or None


rows = []
for b in bronze:
    o = json.loads(b["raw_json"]).get("openfda", {})
    rows.append({
        "label_id": b["label_id"],
        "set_id": b["set_id"],
        "label_version": b["version"],
        "effective_time": b["effective_time"],
        "drug": b["drug"],
        "route": joined(o.get("route")) or "UNKNOWN",
        "product_type": joined(o.get("product_type")),
        "brand_names": joined(o.get("brand_name")),
        "manufacturer": joined(o.get("manufacturer_name")),
        "application_number": joined(o.get("application_number")),
    })
meta = pd.DataFrame(rows)  # built from plain dicts: no Spark metrics in DataFrame.attrs
print(f"{len(meta)} labels from {BRONZE} version {BRONZE_VERSION}")

# COMMAND ----------

# MAGIC %md ## 2 · Checks

# COMMAND ----------

assert meta["label_id"].is_unique, "one row per label"
print("labels without route:", int((meta["route"] == "UNKNOWN").sum()))
routes = meta.groupby("drug")["route"].nunique()
print(f"drugs with labels for more than one route: {int((routes > 1).sum())} of {len(routes)}")
display(meta.groupby(["drug", "route"]).size().reset_index(name="labels").sort_values(["drug", "route"]))

# COMMAND ----------

# MAGIC %md ## 3 · Write `label_metadata` and the parquet snapshot

# COMMAND ----------

import uuid
from datetime import datetime, timezone

run_id = str(uuid.uuid4())
out = meta.assign(bronze_table=BRONZE, bronze_delta_version=int(BRONZE_VERSION), metadata_run_id=run_id,
                  created_at=datetime.now(timezone.utc), git_commit=GIT_COMMIT)
spark.createDataFrame(out).write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(TABLE)
version = spark.sql(f"DESCRIBE HISTORY {TABLE} LIMIT 1").collect()[0]["version"]

# Snapshot read back from the table version just written, so the file is an exact copy of it.
snapshot = spark.sql(f"SELECT * FROM {TABLE} VERSION AS OF {version}").toPandas()
snapshot.attrs.clear()  # toPandas() attaches Spark query metrics here; pandas cannot write them to parquet
snapshot["label_metadata_delta_version"] = version
spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.exports")
export_path = f"{EXPORT_DIR}/label_metadata_v{version}.parquet"
snapshot.to_parquet(export_path, index=False)

print(f"Wrote {len(out)} rows to {TABLE} | Delta version {version} | from bronze v{BRONZE_VERSION} | run {run_id}")
print(f"Snapshot: {export_path}")
