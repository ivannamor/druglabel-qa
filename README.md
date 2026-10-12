# DrugLabel QA

A question-answering assistant over official FDA drug labels (anticoagulants / cardiovascular), built for a GxP-style setting: every answer cites the exact label section it comes from, unsupported questions are refused, and low-confidence answers are routed to human review.

> **Status:** work in progress. See the plan below.

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
```

## Repo layout

| Path | Content |
|---|---|
| `notebooks/` | Databricks notebooks: ingest, chunk, embed |
| `src/retrieval/` | Vector, graph, hybrid retrievers |
| `src/kg/` | Relation extraction + Neo4j loading |
| `src/generation/` | Prompts, guardrails, HITL routing |
| `src/eval/` | Golden-set runner, metrics, LLM judge |
| `prompts/` | Versioned prompt files |
| `validation/` | URS, risk assessment, test protocol, traceability matrix, ALCOA+ |

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # then fill in keys
```

LLM provider is set in `.env` (`LLM_PROVIDER=azure_openai | openai | anthropic`).

## Results

_To be added after the evaluation runs (Day 4)._

## Limitations

_To be added._
