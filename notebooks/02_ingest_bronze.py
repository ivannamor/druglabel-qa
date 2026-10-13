# Databricks notebook source
# MAGIC %md
# MAGIC # 02 · Ingest openFDA labels → `bronze_labels`
# MAGIC
# MAGIC Downloads the labels selected in `data/drug_list.csv` and stores each one **unchanged** (raw JSON)
# MAGIC in the Delta table `bronze_labels`, one row per label.
# MAGIC
# MAGIC Per drug: at most `max_labels` single-ingredient prescription labels, most recent first
# MAGIC (ties broken by label id, so the selection is deterministic for a given openFDA snapshot).
# MAGIC
# MAGIC Traceability columns on every row: `ingest_run_id`, `ingested_at`, `openfda_last_updated`,
# MAGIC `drug_list_sha256` (fingerprint of the drug list used) and `git_commit`.
# MAGIC The table is overwritten on each run; earlier runs stay available through Delta time travel.
# MAGIC
# MAGIC **Before running:** upload `data/drug_list.csv` to the volume `<catalog>.<schema>.raw` (see README).

# COMMAND ----------

dbutils.widgets.text("catalog", "workspace")
dbutils.widgets.text("schema", "druglabel_qa")
dbutils.widgets.text("git_commit", "", "git commit of the repo")

CATALOG = dbutils.widgets.get("catalog")
SCHEMA = dbutils.widgets.get("schema")
GIT_COMMIT = dbutils.widgets.get("git_commit").strip() or "unknown"
TABLE = f"{CATALOG}.{SCHEMA}.bronze_labels"
DRUG_LIST_PATH = f"/Volumes/{CATALOG}/{SCHEMA}/raw/drug_list.csv"
FDA_URL = "https://api.fda.gov/drug/label.json"

# COMMAND ----------

# MAGIC %md ## 1 · Setup and connectivity check

# COMMAND ----------

import requests

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {CATALOG}.{SCHEMA}")
spark.sql(f"CREATE VOLUME IF NOT EXISTS {CATALOG}.{SCHEMA}.raw")

r = requests.get(FDA_URL, params={"limit": 1}, timeout=30)
print("openFDA reachable:", r.status_code == 200, "| data last updated:", r.json()["meta"]["last_updated"])

# COMMAND ----------

# MAGIC %md ## 2 · Read the drug list

# COMMAND ----------

import hashlib

import pandas as pd

with open(DRUG_LIST_PATH, "rb") as f:
    drug_list_bytes = f.read()
DRUG_LIST_SHA256 = hashlib.sha256(drug_list_bytes).hexdigest()
drugs = pd.read_csv(DRUG_LIST_PATH)
print(f"{len(drugs)} drugs | drug_list sha256 {DRUG_LIST_SHA256[:12]}…")
display(drugs[["us_name", "atc_code", "role", "available_labels", "max_labels"]])

# COMMAND ----------

# MAGIC %md ## 3 · Download labels

# COMMAND ----------

import json
import time


def fetch_labels(us_name: str, max_labels: int) -> tuple[list[dict], str]:
    """Most recent single-ingredient Rx labels for one drug, plus the openFDA data date."""
    search = f'openfda.generic_name:"{us_name}" AND openfda.product_type:"HUMAN PRESCRIPTION DRUG"'
    results, skip, last_updated = [], 0, ""
    while True:  # page through all matches (openFDA max page size is 1000)
        time.sleep(0.3)
        resp = requests.get(FDA_URL, params={"search": search, "limit": 1000, "skip": skip}, timeout=120)
        resp.raise_for_status()
        body = resp.json()
        last_updated = body["meta"]["last_updated"]
        results += body["results"]
        skip += 1000
        if skip >= body["meta"]["results"]["total"]:
            break
    single = [x for x in results if len(x.get("openfda", {}).get("substance_name", [])) == 1]
    single.sort(key=lambda x: (x.get("effective_time", ""), x["id"]), reverse=True)
    return single[:max_labels], last_updated


rows = []
for d in drugs.itertuples():
    labels, last_updated = fetch_labels(d.us_name, int(d.max_labels))
    for rank, label in enumerate(labels, start=1):
        rows.append({
            "label_id": label["id"],
            "set_id": label["set_id"],
            "version": label.get("version"),
            "effective_time": label.get("effective_time"),
            "drug": d.us_name,
            "atc_code": d.atc_code,
            "role": d.role,
            "recency_rank": rank,
            "raw_json": json.dumps(label, ensure_ascii=False),
            "openfda_last_updated": last_updated,
        })
    print(f"{d.us_name:<22} {len(labels):>3} labels")
print(f"\nTotal: {len(rows)} labels")

# COMMAND ----------

# MAGIC %md ## 4 · Write `bronze_labels` and record the Delta version

# COMMAND ----------

import uuid
from datetime import datetime, timezone

from pyspark.sql import functions as F

run_id = str(uuid.uuid4())
ingested_at = datetime.now(timezone.utc)

df = (spark.createDataFrame(pd.DataFrame(rows))
      .withColumn("ingest_run_id", F.lit(run_id))
      .withColumn("ingested_at", F.lit(ingested_at))
      .withColumn("drug_list_sha256", F.lit(DRUG_LIST_SHA256))
      .withColumn("git_commit", F.lit(GIT_COMMIT)))

dupes = df.groupBy("label_id").count().filter("count > 1").count()
assert dupes == 0, f"{dupes} labels selected for more than one drug"

df.write.mode("overwrite").option("overwriteSchema", "true").saveAsTable(TABLE)

version = spark.sql(f"DESCRIBE HISTORY {TABLE} LIMIT 1").collect()[0]["version"]
print(f"Wrote {df.count()} rows to {TABLE} | Delta version {version} | run {run_id}")

# COMMAND ----------

display(spark.table(TABLE).groupBy("role").agg(F.countDistinct("drug").alias("drugs"), F.count("*").alias("labels")))
