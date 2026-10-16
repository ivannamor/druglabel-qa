"""Evaluation runner: every golden-set question in each configuration (retrieval mode x answer prompt).

Per question it records the answer, status, citations, latency, tokens and cost, and computes:
- refusals (computed): an unanswerable item is correct if the system refuses with the expected token;
  an answerable item answered with a refusal is a false refusal;
- citation validity (computed): no invalid citations;
- citation of a gold passage (computed): a cited passage is a gold passage or a copy of one
  (same drug, same text or near-identical);
- retrieval hit (computed): a gold passage, or a copy, is among the retrieved passages;
- correctness and faithfulness (judged, `src/eval/judge.py`).
Repeats (`--repeats 3`) measure consistency; paraphrased items (`paraphrase_of`) measure robustness.

Every configuration is one MLflow run (parameters, metrics, per-question results); LLM responses and
verdicts are cached, so an interrupted run resumes where it stopped at no extra cost. Questions run in
parallel (`--workers`, default 4); generator calls stay spaced by LLM_MIN_INTERVAL_S across threads.

Usage (from repo root):
    python -m src.eval.run --modes vector,graph,hybrid --prompts answer_v1,answer_v2
    python -m src.eval.run --modes hybrid --prompts answer_v2 --repeats 3
"""

import argparse
import hashlib
import json
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from src.eval.judge import JUDGE_PROMPT_VERSION, correctness, faithfulness, judge
from src.generation.answer import answer
from src.generation.llm import cost_usd
from src.retrieval.vector import get_retriever
from src.settings import get_settings
from src.tracing import langfuse, observe

GOLDEN = Path("data/golden_set.jsonl")
OUT_DIR = Path("data/eval")
REFUSALS = {"not_in_labels", "patient_specific"}


@lru_cache
def corpus() -> tuple[pd.DataFrame, np.ndarray]:
    """All chunks (drug, text hash, section, text) and their embeddings, to recognise copies of gold passages."""
    g = pd.read_parquet(get_settings().gold_snapshot_path,
                        columns=["chunk_id", "drug", "section", "text_hash", "text", "embedding"])
    vectors = np.vstack(g["embedding"].to_numpy()).astype(np.float32)
    return g.drop(columns="embedding").reset_index(drop=True), vectors


def same_passage(a: str, b: str) -> bool:
    """True if two chunks are the same passage: same ID, or same drug and section with identical text or
    near-identical embedding (the retriever's near-duplicate rule)."""
    if a == b:
        return True
    g, vectors = corpus()
    idx = pd.Series(g.index, index=g["chunk_id"])
    if a not in idx or b not in idx:
        return False
    ra, rb = g.loc[idx[a]], g.loc[idx[b]]
    if ra.drug != rb.drug or ra.section != rb.section:
        return False
    return ra.text_hash == rb.text_hash or float(vectors[idx[a]] @ vectors[idx[b]]) >= get_settings().dedup_threshold


@observe(name="eval_item", capture_output=False)
def evaluate_item(item: dict, repeat: int) -> dict:
    """One golden-set question: answer and verdict in one Langfuse trace, with the scores attached."""
    row = _evaluate(item, repeat)
    for name in ("correctness", "faithfulness"):
        if row.get(name) is not None:
            langfuse().score_current_trace(name=name, value=row[name],
                                           data_type="CATEGORICAL" if name == "correctness" else "NUMERIC")
    langfuse().update_current_span(metadata={"id": item["id"], "type": item["type"], "repeat": repeat,
                                             "mode": get_settings().retrieval_mode,
                                             "prompt": get_settings().answer_prompt})
    return row


def _evaluate(item: dict, repeat: int) -> dict:
    start = time.time()
    a = answer(item["question"], cache_tag=f"eval-r{repeat}")
    expected = item["expected_behavior"]
    row = {
        "id": item["id"], "type": item["type"], "repeat": repeat, "paraphrase_of": item.get("paraphrase_of"),
        "question": item["question"], "expected_behavior": expected, "status": a.status, "answer": a.text,
        "citations": a.citations, "invalid_citations": a.invalid_citations,
        "retrieved": [c.chunk_id for c in a.retrieved], "graph_facts": len(a.graph_facts),
        "model": a.llm.model, "input_tokens": a.llm.input_tokens, "output_tokens": a.llm.output_tokens,
        "llm_latency_s": a.llm.latency_s, "cost_usd": cost_usd(a.llm.model, a.llm.input_tokens, a.llm.output_tokens),
        "trace_id": langfuse().get_current_trace_id(),
    }
    if expected in REFUSALS:
        row["refusal_correct"] = a.status == expected
        row["correctness"] = "correct" if a.status == expected else "incorrect"
        return row

    gold = item["gold_chunk_ids"]
    row["false_refusal"] = a.status in REFUSALS
    row["citations_valid"] = not a.invalid_citations
    row["cites_gold"] = any(same_passage(c, g) for c in a.citations for g in gold)
    row["retrieval_hit"] = any(same_passage(c.chunk_id, g) for c in a.retrieved for g in gold)
    if a.status in REFUSALS:
        row["correctness"] = "incorrect"
        return row
    texts = {c.chunk_id: c.text for c in a.retrieved}
    verdict = judge(item["question"], item["expected_answer"], item["key_facts"], a.text,
                    {cid: texts[cid] for cid in a.citations if cid in texts})
    row.update({"correctness": correctness(verdict), "faithfulness": faithfulness(verdict),
                "key_facts_present": verdict.key_facts_present, "judge_explanation": verdict.explanation})
    row["eval_latency_s"] = round(time.time() - start, 2)
    return row


def summarize(rows: pd.DataFrame) -> dict[str, float]:
    ans = rows[rows["expected_behavior"] == "answer"]
    una = rows[rows["expected_behavior"] != "answer"]
    original = ans[ans["paraphrase_of"].isna()]
    m = {
        "questions": rows["id"].nunique(),
        "correct_rate": (original["correctness"] == "correct").mean(),
        "correct_or_partial_rate": original["correctness"].isin(["correct", "partial"]).mean(),
        "faithfulness": original["faithfulness"].dropna().mean(),
        "citation_validity": original["citations_valid"].mean(),
        "cites_gold_rate": original["cites_gold"].mean(),
        "retrieval_hit_rate": original["retrieval_hit"].mean(),
        "false_refusal_rate": original["false_refusal"].mean(),
        "correct_refusal_rate": una["refusal_correct"].mean() if len(una) else float("nan"),
        "latency_p50_s": rows["llm_latency_s"].median(),
        "latency_p95_s": rows["llm_latency_s"].quantile(0.95),
        "cost_usd_total": rows["cost_usd"].sum(),
        "cost_usd_per_question": rows["cost_usd"].mean(),
    }
    for qtype in ("single_fact", "multi_hop"):
        sub = original[original["type"] == qtype]
        m[f"correct_rate_{qtype}"] = (sub["correctness"] == "correct").mean() if len(sub) else float("nan")
    para = ans[ans["paraphrase_of"].notna()]
    if len(para):  # robustness: same correctness label on the paraphrase as on its original
        orig = original.groupby("id")["correctness"].first()
        m["robustness"] = np.mean([orig.get(p.paraphrase_of) == p.correctness for p in para.itertuples()])
    if rows["repeat"].nunique() > 1:  # consistency: same status and correctness in every repeat
        m["consistency"] = rows.groupby("id").apply(
            lambda g: g["status"].nunique() == 1 and g["correctness"].nunique() == 1).mean()
    return {k: (round(float(v), 4) if v == v else None) for k, v in m.items()}  # v == v drops NaN


def run_config(items: list[dict], mode: str, prompt: str, repeats: int, log: bool, workers: int = 4) -> dict:
    s = get_settings()
    s.retrieval_mode, s.answer_prompt = mode, prompt  # settings are one shared object; set per configuration
    corpus(), get_retriever()  # load shared resources once, before the worker threads start
    jobs = [(item, r) for r in range(1, repeats + 1) for item in items]
    rows, done = [], 0
    with ThreadPoolExecutor(max_workers=workers) as pool:  # results come back in job order
        for row in pool.map(lambda job: evaluate_item(*job), jobs):
            rows.append(row)
            done += 1
            print(f"\r{mode}/{prompt}: {done}/{len(jobs)}", end="", flush=True)
    print()
    df = pd.DataFrame(rows)
    summary = summarize(df)
    name = f"{mode}_{prompt}_r{repeats}"
    out = OUT_DIR / name
    out.mkdir(parents=True, exist_ok=True)
    df.to_json(out / "results.jsonl", orient="records", lines=True)
    (out / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if log:
        log_mlflow(name, df, summary, out, mode, prompt, repeats)
    langfuse().flush()
    return {"config": name, **summary}


def log_mlflow(name: str, df: pd.DataFrame, summary: dict, out: Path, mode: str, prompt: str, repeats: int) -> None:
    import mlflow

    from src.generation.answer import load_prompt
    from src.tracking import config_params, git_state, init_tracking
    init_tracking()
    commit, dirty = git_state()
    s = get_settings()
    with mlflow.start_run(run_name=f"eval {name}"):
        mlflow.set_tags({"run_type": "evaluation", "git_commit": commit, "git_dirty": str(dirty)})
        mlflow.log_params({**config_params(), "prompt_name": prompt, "prompt_sha256": load_prompt(prompt)[1],
                           "repeats": repeats, "judge_provider": s.judge_provider, "judge_model": s.judge_model,
                           "judge_prompt_version": JUDGE_PROMPT_VERSION,
                           "golden_set_sha256": hashlib.sha256(GOLDEN.read_bytes()).hexdigest(),
                           "models_used": ",".join(sorted(df["model"].unique()))})
        mlflow.log_metrics({k: v for k, v in summary.items() if v is not None})
        mlflow.log_artifacts(str(out), "eval")


def load_items(limit: int | None) -> list[dict]:
    items = [json.loads(line) for line in GOLDEN.read_text(encoding="utf-8").splitlines()]
    return items[:limit] if limit else items


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--modes", default="vector,graph,hybrid")
    p.add_argument("--prompts", default="answer_v1,answer_v2")
    p.add_argument("--repeats", type=int, default=1)
    p.add_argument("--limit", type=int, help="first N items only (smoke test)")
    p.add_argument("--workers", type=int, default=4, help="questions evaluated in parallel")
    p.add_argument("--no-log", action="store_true", help="do not log to MLflow")
    args = p.parse_args()
    items = load_items(args.limit)
    print(f"{len(items)} items", dict(Counter(i["type"] for i in items)))
    table = [run_config(items, m, pr, args.repeats, not args.no_log, args.workers)
             for m in args.modes.split(",") for pr in args.prompts.split(",")]
    result = pd.DataFrame(table).set_index("config")
    print(result.T.to_string())
    result.to_csv(OUT_DIR / f"comparison_r{args.repeats}.csv")
