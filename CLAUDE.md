# CLAUDE.md — DrugLabel QA

> Project brief used to direct Claude Code during development. Kept as written, plus the status column; decisions that departed from it (for example the `DrugClass` node, paid LLM APIs, a 71-item golden set) are recorded with their reasons in the [CHANGELOG](CHANGELOG.md).

## Purpose of this repo

Portfolio project built in ~6 days, set in **pharma / life sciences (GxP-regulated)** AI engineering. It covers: LLM/RAG solutions, LLM evaluation, Databricks, MLflow, Neo4j / knowledge graphs, Langfuse, and GxP-style validation, traceability and audit readiness.

**Priorities, in order:**
1. Something small that runs end to end beats something ambitious and half-finished.
2. Traceability and evaluation are the headline features. Never cut them.
3. Code should be readable by a reviewer opening the repo for 5 minutes.

## What the system does

An assistant that answers questions about official drug labels (e.g., for a medical information or pharmacovigilance team).
- Every answer cites the exact label section (chunk ID) it comes from.
- It refuses when the retrieved context does not support an answer.
- It declines patient-specific dosing advice and flags out-of-scope questions (drugs not in the dataset).
- Low-confidence or uncited answers go to a human review queue instead of being returned as final.

## Data

- Source: **openFDA drug label API** (public, free). Labels are already split into sections (indications, contraindications, warnings, adverse reactions, drug interactions, etc.).
- Scope: **200–300 labels from one therapeutic area** (default: anticoagulants / cardiovascular). Keep it small.
- Every chunk keeps: `label_id`, `set_id`/label version, `drug_name`, `section`, `chunk_id`.

## Architecture

```
openFDA labels (JSON)
      │
      ▼
[Databricks] Bronze: raw JSON → Silver: sections + chunks → Gold: embeddings
      │                                   │
      │                                   ▼
      │                     LLM extraction of entities/relations
      │                                   │
      ▼                                   ▼
 Vector retrieval                  [Neo4j] Knowledge graph
      │                                   │
      └──────────► Hybrid retriever ◄─────┘
                         │
                         ▼
     Answer generation + guardrails (citations, refusal, scope)
                         │
           ┌─────────────┼──────────────┐
           ▼             ▼              ▼
     [Langfuse]      [MLflow]     Review queue (HITL)
     traces, cost   prompts, runs,   low-confidence answers
     latency        evals, approvals  → Delta table
```

### Components

**1. Data pipeline (Databricks Free Edition)**
- Delta tables: `bronze_labels` (raw), `silver_chunks` (cleaned sections, chunked), `gold_embeddings`.
- Record the Delta table version used in every run (reproducibility).
- If a Databricks feature is unavailable on Free Edition (e.g., managed Vector Search), fall back to computing similarity in the notebook or FAISS, and document it in the README.

**2. Knowledge graph (Neo4j AuraDB Free)**
- Schema:
  - `(Drug)-[:INDICATED_FOR]->(Condition)`
  - `(Drug)-[:HAS_ADVERSE_REACTION]->(AdverseEvent)`
  - `(Drug)-[:INTERACTS_WITH]->(Drug)`
  - `(Drug)-[:CONTRAINDICATED_IN]->(Condition)`
- Relations are extracted by an LLM from label sections.
- **Every edge stores `source_chunk_id` and `extraction_run_id`.** Do not create edges without them.
- Normalize entity names (lowercase, strip, simple synonym handling). No external ontology needed.

**3. Retrieval and generation**
- Three retrieval modes, selectable via config: `vector`, `graph`, `hybrid`.
- Guardrails:
  - each claim must cite a chunk ID
  - refuse when context is insufficient
  - decline patient-specific dosing advice
  - flag drugs/questions outside the dataset
- HITL: if grounding confidence is below threshold or the answer has no citations, write it to a `review_queue` table.

**4. MLflow**
- Prompts are versioned files in `prompts/` (or MLflow prompt registry if available).
- Every run logs: model name, provider, prompt version, parameters, dataset / Delta version, git commit hash, evaluation scores.
- Simulated approval step: a config is "released" only if it passes acceptance thresholds; tag it with `validation_status=approved`, `approved_by`, `approval_date`.

**5. Langfuse**
- Trace every LLM call and retrieval step (latency, tokens, cost).
- Document at least one real root cause analysis in the README (bad answer → trace → cause → fix).

**6. Evaluation**
- Golden set: ~60 questions in `data/golden_set.jsonl`, three types: `single_fact`, `multi_hop`, `unanswerable`.
- Metrics:
  - correctness (LLM-as-judge + manual check on a sample to validate the judge)
  - grounding / faithfulness (every claim supported by its cited chunk)
  - citation accuracy
  - consistency (each question run 3 times, agreement)
  - robustness (paraphrased variants)
  - correct refusal rate on `unanswerable`
  - latency and cost (from Langfuse)
- Output: comparison table vector vs graph vs hybrid, and prompt v1 vs v2.

**7. Validation pack (`validation/`)**
- `URS.md`: 10–15 user requirements, IDs `REQ-01`, `REQ-02`, …
- `risk_assessment.md`: lightweight FMEA (hallucination, wrong drug confusion, outdated label, prompt injection in source text, missed interaction) with severity, likelihood, mitigation.
- `test_protocol.md`: test cases `TC-01`, … mapped to requirements, with acceptance criteria (e.g., grounding ≥ 0.90, correct refusal ≥ 0.95).
- `traceability_matrix.csv`: `req_id, test_id, mlflow_run_id, result, status`.
- `alcoa_mapping.md`: how the system addresses each ALCOA+ principle.
- `CHANGELOG.md` at repo root, plus a git tag per release.

## Repo structure

```
druglabel-qa/
├── CLAUDE.md
├── README.md              # goal, architecture, results table, limitations
├── CHANGELOG.md
├── notebooks/             # Databricks notebooks: ingest, chunk, embed
├── scripts/               # local one-off scripts: data exploration, drug selection
├── src/
│   ├── retrieval/         # vector, graph, hybrid
│   ├── kg/                # extraction + Neo4j loading
│   ├── generation/        # prompts, guardrails, HITL routing
│   └── eval/              # golden set runner, metrics, judge
├── prompts/               # versioned prompt files (e.g., answer_v1.md)
├── data/golden_set.jsonl
└── validation/            # URS, risk, test protocol, traceability, ALCOA+
```

## Conventions

- Python 3.12. Type hints on public functions. Small modules over large ones.
- Config via a single settings module + `.env`. **Never commit secrets**; keep `.env.example` up to date.
- LLM provider is a config value (OpenAI / Anthropic / Azure OpenAI). Switching to Azure must be a one-line change.
- Every pipeline or eval run must be reproducible from: git commit + prompt version + dataset version + config. If a change breaks this, flag it.
- IDs are stable and human-readable: `REQ-xx`, `TC-xx`, `chunk_id = {label_id}:{section}:{n}`.
- When adding a requirement or test, update `traceability_matrix.csv` in the same change.
- Commits: small and descriptive. Update `CHANGELOG.md` for anything that changes behavior or results.

## How to work with me (Ivan)

- Work one plan step at a time. Before large changes (new dependency, restructuring, schema change), explain the plan briefly and wait for confirmation.
- When editing existing text or docs, change only what I asked for. Don't rephrase untouched parts.
- If a tool or free tier doesn't support something, say so and propose the simplest fallback.
- Explain non-obvious design choices in a short comment or in the README, not in long chat messages.

## Plan and status

| Day | Work | Done when | Status |
|---|---|---|---|
| 1 | Repo, README plan, Databricks Free Edition, ingest 200–300 labels into bronze/silver | Chunks with metadata exist in a Delta table | ☑ |
| 2 | Embeddings, vector retrieval, first RAG answers, MLflow logging | One question answered with citations, run visible in MLflow | ☑ |
| 3 | Relation extraction, Neo4j graph, graph + hybrid retrieval | A multi-hop question answered correctly via the graph | ☑ |
| 4 | Langfuse tracing, golden set, evaluation runner | Results table for all three retrieval modes | ☑ |
| 5 | Guardrails, HITL queue, validation pack | Traceability matrix links every requirement to a test and a run | ☑ |
| 6 | README with diagram and results, one root cause analysis write-up | Repo public and presentable | ☑ |

**If time runs short, cut in this order:** HITL queue → ALCOA+ mapping → robustness metric. **Never cut:** traceability matrix, evaluation table.
