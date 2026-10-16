"""Langfuse tracing: one trace per answered question, with a span per retrieval step and a generation
per LLM call (model, tokens, cost, latency). Not to be confused with `src/tracking.py`, which logs
runs, parameters and metrics to MLflow.

Without Langfuse keys in `.env` tracing is disabled and the code runs unchanged. Import `observe` from
here, not from `langfuse`, so the client is configured from settings before any traced call.
"""

from langfuse import Langfuse, get_client, observe  # noqa: F401  (observe is re-exported)

from src.settings import get_settings

_s = get_settings()
_enabled = bool(_s.langfuse_public_key and _s.langfuse_secret_key)
Langfuse(
    public_key=_s.langfuse_public_key or "tracing-disabled",  # placeholder avoids a warning when keys are unset
    secret_key=_s.langfuse_secret_key.get_secret_value() if _s.langfuse_secret_key else "tracing-disabled",
    base_url=_s.langfuse_host,
    tracing_enabled=_enabled,
)


def langfuse() -> Langfuse:
    return get_client()


def trace_url() -> str | None:
    """Link to the current trace in the Langfuse UI (None when tracing is off)."""
    return langfuse().get_trace_url() if _enabled else None
