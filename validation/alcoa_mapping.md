# ALCOA+ mapping

How DrugLabel QA addresses each data-integrity principle (ALCOA+: Attributable, Legible, Contemporaneous,
Original, Accurate, plus Complete, Consistent, Enduring, Available). Evidence points to where it can be checked.

| Principle | How it is met | Evidence |
|---|---|---|
| **Attributable** | Code changes have a git author; every data-layer row and every run records the git commit that produced it; golden-set items record drafting model, reviewer and review date; approvals record approver and date; held answers record the model that actually answered. | `git log`; `git_commit` columns in Bronze/Silver/Gold/label metadata; `reviewed_by` in `data/golden_set.jsonl`; `approved_by` tag in MLflow; approval tables in `validation/` |
| **Legible** | Human-readable IDs (`REQ-xx`, `TC-xx`, `GS-xxx`, `chunk_id = {label_id}:{section}:{n}`); plain-text formats (Markdown, CSV, JSONL); answers cite readable chunk IDs. | `validation/`, `data/golden_set.jsonl`, `data/eval/` |
| **Contemporaneous** | Timestamps written when the event happens: ingest, chunking, embedding, review queue entries, MLflow runs, Langfuse traces. | `ingested_at`, `chunked_at`, `embedded_at`, `created_at` columns; MLflow and Langfuse timestamps |
| **Original** | Raw openFDA JSON kept unchanged in Bronze (single version, never modified); golden-set drafts and the review sheet kept next to the approved set; the previous expected answer kept when an item is revised. | `bronze_labels` history (TC-14); `data/golden/`; `expected_answer_v1_0` |
| **Accurate** | Every relation in the graph is backed by a verbatim quote; every citation checked against the retrieved passages; answers that fail checks are held; golden set reviewed against source passages; the judge validated against blind human grades. | `src/kg/extract.py`; `src/generation/guardrails.py`; `validation/golden_set_review.md`; `data/eval/judge_validation/result.json` |
| **Complete** | Rejected relations, rejected golden items, held answers and failed tests are kept with their reason, not deleted; the evaluation keeps every per-question result. | `rejected.jsonl` of each extraction; review decisions; `review_queue`; `traceability_matrix.csv` |
| **Consistent** | Same pipeline and IDs end to end; each layer records the version of the layer it was built from; dated model snapshot; prompt identified by name and hash; files written with LF so hashes match the repository. | `bronze_delta_version` / `silver_delta_version` columns; `prompt_sha256`; `golden_set_sha256` |
| **Enduring** | Delta tables with time travel; git history; MLflow runs and artifacts in the Databricks workspace; Langfuse traces. | `DESCRIBE HISTORY`; tag `v1.0.0`; MLflow experiment `druglabel-qa-runs` |
| **Available** | Any answer can be traced back from its MLflow run or review-queue row to the trace, the prompt, the passages and the label version; documentation in the repository. | MLflow UI, Langfuse UI, `review_queue` table, README |
