"""Human-in-the-loop review queue: answers held by the guardrails go to a Delta table on Databricks
instead of to the user.

Rows are written through the workspace's serverless SQL warehouse (Databricks SDK statement execution, with
query parameters). Each row keeps what a reviewer needs and what an audit needs: question, answer, reasons,
citations, model, prompt version and hash, data version, git commit and the Langfuse trace.

Usage (from repo root): python -m src.generation.hitl   # create the table if needed and show pending items
"""

import json
import uuid
from datetime import datetime, timezone
from functools import lru_cache

from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementParameterListItem, StatementState

from src.generation.answer import Answer
from src.generation.guardrails import GuardrailResult
from src.settings import get_settings

COLUMNS = {
    "review_id": "STRING", "created_at": "TIMESTAMP", "status": "STRING", "question": "STRING",
    "answer": "STRING", "reasons": "STRING", "grounding": "DOUBLE", "citations": "STRING",
    "cited_drugs": "STRING", "retrieval_mode": "STRING", "model": "STRING", "prompt_name": "STRING",
    "prompt_sha256": "STRING", "gold_delta_version": "INT", "git_commit": "STRING", "trace_id": "STRING",
    "reviewed_by": "STRING", "reviewed_at": "TIMESTAMP", "review_decision": "STRING", "review_notes": "STRING",
}


def table() -> str:
    s = get_settings()
    return f"{s.databricks_catalog}.{s.databricks_schema}.review_queue"


@lru_cache
def _client() -> tuple[WorkspaceClient, str]:
    s = get_settings()
    w = WorkspaceClient(host=s.databricks_host, token=s.databricks_token.get_secret_value())
    warehouse = next(iter(w.warehouses.list())).id  # Free Edition: one serverless starter warehouse
    columns = ", ".join(f"{name} {kind}" for name, kind in COLUMNS.items())
    _sql(w, warehouse, f"CREATE TABLE IF NOT EXISTS {table()} ({columns}) "
                       "COMMENT 'Answers held by the guardrails for human review'")
    return w, warehouse


def _sql(w: WorkspaceClient, warehouse: str, statement: str, params: list[StatementParameterListItem] | None = None):
    r = w.statement_execution.execute_statement(warehouse_id=warehouse, statement=statement, parameters=params,
                                                wait_timeout="50s")
    if r.status.state != StatementState.SUCCEEDED:
        raise RuntimeError(f"review queue SQL failed: {r.status.state} {r.status.error}")
    return r


def enqueue(a: Answer, guard: GuardrailResult, git_commit: str, gold_version: int, trace_id: str | None) -> str:
    """Write one held answer to the review queue; returns its review_id."""
    w, warehouse = _client()
    review_id = str(uuid.uuid4())
    values = {
        "review_id": review_id, "created_at": datetime.now(timezone.utc).isoformat(), "status": "pending",
        "question": a.question, "answer": a.text, "reasons": json.dumps(guard.reasons),
        "grounding": guard.grounding, "citations": json.dumps(a.citations), "cited_drugs": json.dumps(guard.cited_drugs),
        "retrieval_mode": a.retrieval_mode, "model": a.llm.model, "prompt_name": a.prompt_name,
        "prompt_sha256": a.prompt_sha256, "gold_delta_version": gold_version, "git_commit": git_commit,
        "trace_id": trace_id,
    }
    params = [StatementParameterListItem(name=k, value=None if v is None else str(v), type=COLUMNS[k])
              for k, v in values.items()]
    _sql(w, warehouse, f"INSERT INTO {table()} ({', '.join(values)}) VALUES ({', '.join(':' + k for k in values)})",
         params)
    return review_id


def pending(limit: int = 20) -> list[list[str]]:
    w, warehouse = _client()
    r = _sql(w, warehouse, f"SELECT created_at, review_id, reasons, question FROM {table()} "
                           f"WHERE status = 'pending' ORDER BY created_at DESC LIMIT {int(limit)}")
    return (r.result.data_array or []) if r.result else []


if __name__ == "__main__":
    rows = pending()
    print(f"{table()}: {len(rows)} pending (latest first)")
    for row in rows:
        print(" | ".join(str(x)[:80] for x in row))
