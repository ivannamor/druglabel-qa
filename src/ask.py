"""Ask one question end to end and log it as an MLflow run on Databricks.

Usage (from repo root): python -m src.ask "What is the antidote for dabigatran?"
"""

import sys
import time
from dataclasses import asdict

import mlflow

from src.generation.answer import Answer, answer, load_prompt
from src.tracking import config_params, git_state, init_tracking


def log_answer(a: Answer, total_latency_s: float) -> str:
    """Log one answer with everything needed to reproduce and audit it; return the MLflow run ID."""
    init_tracking()
    commit, dirty = git_state()
    with mlflow.start_run(run_name=f"ask: {a.question[:60]}") as run:
        mlflow.set_tags({"run_type": "ask", "git_commit": commit, "git_dirty": str(dirty),
                         "status": a.status, "model_used": a.llm.model})
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
        })
        mlflow.log_dict(asdict(a), "answer.json")  # question, answer, citations, retrieved passages, LLM usage
        mlflow.log_text(load_prompt(a.prompt_name)[0], f"prompts/{a.prompt_name}.md")
    return run.info.run_id


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What is the antidote for dabigatran?"
    start = time.time()
    a = answer(question)
    run_id = log_answer(a, round(time.time() - start, 2))

    print(f"{a.text}\n")
    print(f"status: {a.status} | citations: {len(a.citations)} valid, {len(a.invalid_citations)} invalid "
          f"| model: {a.llm.model}")
    print(f"MLflow run: {run_id}")
    if git_state()[1]:
        print("WARNING: uncommitted changes; this run is not reproducible from its git commit.")
