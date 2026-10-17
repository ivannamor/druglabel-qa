"""Calibrate the grounding threshold of the guardrails on evaluation results, and preview routing.

The grounding score (`src/generation/guardrails.py`) is a cheap lexical proxy; the validated LLM judge's
faithfulness is the reference: an answer with an unsupported claim (faithfulness < 1) should score low.
For each candidate threshold this reports how many answers with unsupported claims are caught and how
many fully supported answers are held needlessly. Output: data/eval/guardrail_calibration.json.

Usage (from repo root): python -m src.eval.calibrate_guardrails
"""

import json
from pathlib import Path

import pandas as pd

from src.eval.run import OUT_DIR
from src.generation.answer import Answer
from src.generation.guardrails import check, grounding
from src.retrieval.vector import RetrievedChunk
from src.settings import get_settings

CONFIGS = ["vector_answer_v1_r1", "vector_answer_v2_r1", "graph_answer_v1_r1", "graph_answer_v2_r1",
           "hybrid_answer_v1_r1", "hybrid_answer_v2_r1"]


def load_answers() -> pd.DataFrame:
    chunks = pd.read_parquet(get_settings().gold_snapshot_path, columns=[
        "chunk_id", "label_id", "effective_time", "drug", "section", "subsection", "text"]).set_index("chunk_id")
    rows = []
    for config in CONFIGS:
        df = pd.read_json(OUT_DIR / config / "results.jsonl", lines=True)
        for r in df[df["status"] == "answered"].itertuples():
            passages = {c: chunks.loc[c, "text"] for c in r.citations if c in chunks.index}
            rows.append({"config": config, "id": r.id, "question": r.question, "answer": r.answer,
                         "status": r.status, "citations": r.citations, "invalid": r.invalid_citations,
                         "retrieved": r.retrieved, "grounding": grounding(r.answer, passages),
                         "faithfulness": r.faithfulness, "correctness": r.correctness})
    return pd.DataFrame(rows)


def as_answer(row, chunks: pd.DataFrame) -> Answer:
    retrieved = [RetrievedChunk(c, chunks.loc[c, "label_id"], chunks.loc[c, "effective_time"], chunks.loc[c, "drug"],
                                chunks.loc[c, "section"], None, chunks.loc[c, "text"], 0.0, 1)
                 for c in row.retrieved if c in chunks.index]
    return Answer(row.question, row.answer, row.status, row.citations, row.invalid_citations, retrieved, [], "", "", "", None)


def main() -> None:
    df = load_answers()
    judged = df[df["faithfulness"].notna()]
    unsupported = judged["faithfulness"] < 1
    table = []
    for t in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8]:
        held = judged["grounding"] < t
        table.append({"threshold": t,
                      "unsupported_caught": round(float((held & unsupported).sum() / max(1, unsupported.sum())), 3),
                      "supported_held": round(float((held & ~unsupported).sum() / max(1, (~unsupported).sum())), 3)})
    print(f"{len(judged)} judged answers, {int(unsupported.sum())} with an unsupported claim")
    print(pd.DataFrame(table).to_string(index=False))

    # routing preview for the release configuration with the configured threshold
    chunks = pd.read_parquet(get_settings().gold_snapshot_path, columns=[
        "chunk_id", "label_id", "effective_time", "drug", "section", "text"]).set_index("chunk_id")
    release = pd.read_json(OUT_DIR / "hybrid_answer_v2_r1" / "results.jsonl", lines=True)
    release = release[release["expected_behavior"] == "answer"]
    outcomes = []
    for r in release.itertuples():
        g = check(r.question, as_answer(r, chunks)) if r.status == "answered" else None
        outcomes.append({"id": r.id, "type": r.type, "correctness": r.correctness,
                         "released": g.released if g else True, "reasons": g.reasons if g else [r.status]})
    o = pd.DataFrame(outcomes)
    preview = {
        "answerable_items": len(o), "released": int(o["released"].sum()),
        "released_incorrect": int((o["released"] & (o["correctness"] == "incorrect")).sum()),
        "held_incorrect": int((~o["released"] & (o["correctness"] == "incorrect")).sum()),
        "held_correct": int((~o["released"] & (o["correctness"] == "correct")).sum()),
        "reasons": pd.Series([x for rs in o["reasons"] for x in rs]).value_counts().to_dict(),
    }
    print("\nrouting preview (hybrid v2, answerable items):", json.dumps(preview, indent=1))
    out = {"min_grounding": get_settings().min_grounding, "threshold_table": table, "routing_preview": preview}
    Path(OUT_DIR / "guardrail_calibration.json").write_text(json.dumps(out, indent=2), encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
