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

## LLM providers

Providers are config values in `.env`; switching is a one-line change.

| Role | Demo setup (free) | Production target |
|---|---|---|
| Generation + KG extraction | `gemma-4-31b-it` via Google AI Studio (free tier) | Azure OpenAI (EU Data Zone deployment) |
| LLM-as-judge | `gemini-3.5-flash-lite`, fallback `gemini-3.1-flash-lite` (free tier) | Azure OpenAI, stronger model than the generator |
| Embeddings | `BAAI/bge-small-en-v1.5` (open source, run on Databricks) | Same, or Azure OpenAI embeddings |

Why: the project runs at zero cost through one OpenAI-compatible endpoint, and a pinned open-source embedding model keeps runs reproducible. Gemma has the highest free daily quota (bulk work); the judge is a different, stronger model.

Known trade-offs:
- Generator and judge come from the same vendor (open-weight Gemma vs proprietary Gemini), so the judge is not fully independent. It is validated against human labels on a sample before its scores are trusted.
- Free tiers are rate-limited and occasionally overloaded (HTTP 503), so LLM responses are cached, calls retry with backoff, and evaluation may run over more than one day.

## Results

_To be added after the evaluation runs (Day 4)._

## Limitations

_To be added._
