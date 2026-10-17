"""Ask one question end to end: answer, guardrails, release or human review queue, MLflow run.

An answer the guardrails hold is not shown as final: it is written to the review queue (Delta table
`review_queue`) and the user is told it awaits review.

Usage (from repo root): python -m src.ask "What is the antidote for dabigatran?"
"""

import sys
import time
from dataclasses import asdict

import mlflow

from src.generation.answer import Answer, answer, load_prompt
from src.generation.guardrails import GuardrailResult, check
from src.generation.hitl import enqueue
from src.retrieval.vector import get_retriever
from src.tracing import langfuse, observe
from src.tracking import config_params, git_state, init_tracking


@observe(name="ask", capture_output=False)
def ask(question: str) -> tuple[Answer, GuardrailResult, str | None, str | None]:
    """(answer, guardrail result, review_id if held, Langfuse trace ID)."""
    a = answer(question)
    guard = check(question, a)
    trace_id = langfuse().get_current_trace_id()
    review_id = None
    if not guard.released:
        review_id = enqueue(a, guard, git_state()[0], get_retriever().gold_version, trace_id)
    langfuse().update_current_span(output={"released": guard.released, "reasons": guard.reasons,
                                           "review_id": review_id})
    return a, guard, review_id, trace_id


def log_answer(a: Answer, guard: GuardrailResult, review_id: str | None, total_latency_s: float) -> str:
    """Log one answer with everything needed to reproduce and audit it; return the MLflow run ID."""
    init_tracking()
    commit, dirty = git_state()
    with mlflow.start_run(run_name=f"ask: {a.question[:60]}") as run:
        mlflow.set_tags({"run_type": "ask", "git_commit": commit, "git_dirty": str(dirty),
                         "status": a.status, "model_used": a.llm.model,
                         "released": str(guard.released), "guardrail_reasons": ",".join(guard.reasons),
                         "review_id": review_id or ""})
        mlflow.log_params({**config_params(), "prompt_name": a.prompt_name, "prompt_sha256": a.prompt_sha256})
        mlflow.log_metrics({
            "latency_s": total_latency_s,
            "llm_latency_s": a.llm.latency_s,
            "input_tokens": a.llm.input_tokens,
            "output_tokens": a.llm.output_tokens,
            "n_citations": len(a.citations),
            "n_invalid_citations": len(a.invalid_citations),
            "top_retrieval_score": a.retrieved[0].score if a.retrieved else 0.0,
            "n_passages": len(a.retrieved),
            "n_graph_facts": len(a.graph_facts),
            **({"grounding": guard.grounding} if guard.grounding is not None else {}),
        })
        mlflow.log_dict({**asdict(a), "guardrails": asdict(guard)}, "answer.json")
        mlflow.log_text(load_prompt(a.prompt_name)[0], f"prompts/{a.prompt_name}.md")
    return run.info.run_id


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What is the antidote for dabigatran?"
    start = time.time()
    a, guard, review_id, _ = ask(question)
    run_id = log_answer(a, guard, review_id, round(time.time() - start, 2))
    langfuse().flush()

    if guard.released:
        print(f"{a.text}\n")
    else:
        print(f"Answer held for human review ({', '.join(guard.reasons)}). Review ID: {review_id}\n")
        print(f"[draft, not released]\n{a.text}\n")
    print(f"status: {a.status} | citations: {len(a.citations)} valid, {len(a.invalid_citations)} invalid "
          f"| grounding: {guard.grounding} | model: {a.llm.model}")
    print(f"MLflow run: {run_id}")
    if git_state()[1]:
        print("WARNING: uncommitted changes; this run is not reproducible from its git commit.")
