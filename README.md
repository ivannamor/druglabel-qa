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

## Data selection

Source: [openFDA drug label API](https://open.fda.gov/apis/drug/label/), prescription labels only.

Scope is **anticoagulation and the drugs that interact with it**: 28 drugs in 13 classes (anticoagulants, antiplatelets, reversal agents, and interaction partners such as amiodarone, verapamil and statins), listed in [`data/drug_list.csv`](data/drug_list.csv). Per drug, at most 10 single-ingredient labels, most recent first (~224 labels).

Why: one drug has up to hundreds of near-identical labels (one per manufacturer), which would flood retrieval with duplicates; combination products mix two drugs in one label (wrong-drug risk); recent labels reduce the outdated-label risk.

Evidence: [`notebooks/00_explore_openfda.py`](notebooks/00_explore_openfda.py) produces [`data/exploration/label_counts.csv`](data/exploration/label_counts.csv) (label counts per candidate, with openFDA data date). Data-quality findings:
- FDA's `pharm_class_epc` is missing for many drugs and wrong for some (e.g., verapamil tagged "ACE inhibitor" via a combination product), so drug classes are assigned manually in `drug_list.csv`.
- Section field names don't always match content (e.g., a `labor_and_delivery` field containing "8.2 Lactation"), parent sections contain their subsections, and some fields hold raw HTML tables. Handled in the Silver step.
- openFDA data changes daily: counts differ slightly between runs, so every ingest records the openFDA `last_updated` date.

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
