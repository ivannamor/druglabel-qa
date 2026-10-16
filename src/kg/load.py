"""Load one extraction run into Neo4j, replacing the current graph.

The graph always holds exactly one extraction run, so every edge's `extraction_run_id` is the same
MLflow run and the graph can be rebuilt from it at any time. Nodes are unique by name per label.
Drugs of the dataset carry `in_dataset=true`, role and ATC code; drugs that only appear as
interaction partners get `in_dataset=false` (used by the scope guardrail).

Usage (from repo root): python -m src.kg.load <extraction_run_id>
"""

import json
import sys
from pathlib import Path

import pandas as pd

from src.kg.extract import OUT_DIR
from src.kg.graph_db import get_driver
from src.settings import get_settings

NODE_LABELS = ["Drug", "DrugClass", "Condition", "AdverseEvent"]
RELATIONS = ["INDICATED_FOR", "CONTRAINDICATED_IN", "HAS_ADVERSE_REACTION", "INTERACTS_WITH"]


def load(run_id: str) -> dict[str, int]:
    s = get_settings()
    rows = [json.loads(line) for line in Path(OUT_DIR / f"extraction_{run_id}" / "accepted.jsonl").read_text(
        encoding="utf-8").splitlines()]
    drugs = (pd.read_parquet(s.gold_snapshot_path, columns=["drug", "role", "atc_code"])
             .drop_duplicates("drug").to_dict("records"))

    def run(query: str, **params) -> None:
        get_driver().execute_query(query, database_=s.neo4j_database, **params)

    run("MATCH (n) DETACH DELETE n")  # one extraction run per graph
    for label in NODE_LABELS:
        run(f"CREATE CONSTRAINT {label.lower()}_name IF NOT EXISTS FOR (n:{label}) REQUIRE n.name IS UNIQUE")
    run("""UNWIND $drugs AS d
           MERGE (n:Drug {name: d.drug}) SET n.in_dataset = true, n.role = d.role, n.atc_code = d.atc_code""",
        drugs=drugs)

    for relation in RELATIONS:  # labels and relation types cannot be query parameters, hence the whitelists
        for target_label in NODE_LABELS:
            batch = [r for r in rows if r["relation"] == relation and r["target_type"] == target_label]
            if not batch:
                continue
            run(f"""UNWIND $rows AS r
                    MATCH (d:Drug {{name: r.drug}})
                    MERGE (t:{target_label} {{name: r.target}})
                    ON CREATE SET t.in_dataset = CASE WHEN '{target_label}' = 'Drug' THEN false ELSE null END
                    MERGE (d)-[e:{relation} {{route: r.route}}]->(t)
                    SET e.source_chunk_id = r.source_chunk_id, e.label_id = r.label_id, e.evidence = r.evidence,
                        e.section = r.section, e.chunk_id_corrected = r.chunk_id_corrected,
                        e.extraction_run_id = $run_id""", rows=batch, run_id=run_id)

    records, _, _ = get_driver().execute_query(
        "MATCH (n) WITH labels(n)[0] AS label, count(*) AS n RETURN label, n ORDER BY label",
        database_=s.neo4j_database)
    counts = {r["label"]: r["n"] for r in records}
    records, _, _ = get_driver().execute_query(
        "MATCH ()-[e]->() RETURN type(e) AS rel, count(*) AS n, count(e.extraction_run_id) AS with_run, "
        "count(e.source_chunk_id) AS with_chunk ORDER BY rel", database_=s.neo4j_database)
    for r in records:
        assert r["n"] == r["with_run"] == r["with_chunk"], f"{r['rel']}: edges without source_chunk_id or run id"
        counts[r["rel"]] = r["n"]
    return counts


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__.splitlines()[-1])
    for name, n in load(sys.argv[1]).items():
        print(f"{name:<22} {n}")
