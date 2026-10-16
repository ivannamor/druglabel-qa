"""Judge validation: compare the judge's correctness labels with blind human grades on a random sample.

Acceptance criterion, fixed before any results (README "Evaluation"): agreement >= 85% on 20 answers.
The grading sheet shows question, expected answer, key facts, the system answer and its cited passages,
never the judge's verdict. The result (agreement, confusion matrix, pass/fail, grader, date) is written to
`data/eval/judge_validation/result.json` and logged as an MLflow run.

Usage (from repo root):
    python -m src.eval.validate_judge sheet            # sample 20 judged answers -> sheet.md
    python -m src.eval.validate_judge score "Name"     # grades in sheet.md -> agreement, MLflow run
"""

import json
import random
import re
import sys
from datetime import date
from pathlib import Path

import pandas as pd

from src.eval.judge import JUDGE_PROMPT_VERSION
from src.eval.run import OUT_DIR
from src.settings import get_settings

DIR = OUT_DIR / "judge_validation"
SAMPLE_SIZE, THRESHOLD, SEED = 20, 0.85, 20261017
LABELS = ("correct", "partial", "incorrect")
HEADER = """# Judge validation: blind grading

For each answer, write one word after `grade:` — correct, partial or incorrect — using the expected answer
and key facts as the reference:
- correct: every key fact is in the system answer and nothing contradicts the expected answer;
- partial: some key facts, nothing contradicting;
- incorrect: no key fact, or something contradicts the expected answer.
The cited passages show what the answer is based on. `notes:` is optional. Do not change the `## J-..` headings.
"""


def judged_rows() -> pd.DataFrame:
    rows = []
    for path in sorted(OUT_DIR.glob("*_r1/results.jsonl")):
        df = pd.read_json(path, lines=True).assign(config=path.parent.name)
        rows.append(df[df["judge_explanation"].notna()] if "judge_explanation" in df else df.iloc[0:0])
    return pd.concat(rows, ignore_index=True)


def make_sheet() -> None:
    judged = judged_rows()
    rng = random.Random(SEED)
    picked, seen = [], set()
    for i in rng.sample(range(len(judged)), len(judged)):  # random order; one answer per question
        row = judged.iloc[i]
        if row["id"] not in seen:
            seen.add(row["id"])
            picked.append(row)
        if len(picked) == SAMPLE_SIZE:
            break
    golden = {i["id"]: i for i in map(json.loads, Path("data/golden_set.jsonl").read_text(encoding="utf-8").splitlines())}
    text = pd.read_parquet(get_settings().gold_snapshot_path, columns=["chunk_id", "text"]).set_index("chunk_id")["text"]

    blocks, sample = [HEADER], []
    for k, row in enumerate(picked, 1):
        item = golden[row["id"]]
        jid = f"J-{k:02d}"
        sample.append({"sample_id": jid, "item_id": row["id"], "config": row["config"],
                       "judge_correctness": row["correctness"], "trace_id": row.get("trace_id")})
        facts = "\n".join(f"- {f}" for f in item["key_facts"])
        cited = "\n\n".join(f"[{c}]\n```text\n{text[c]}\n```" for c in row["citations"]) or "(no citations)"
        blocks.append(f"## {jid}\n\ngrade: \nnotes: \n\n**Question:** {item['question']}\n\n"
                      f"**Expected answer:** {item['expected_answer']}\n\n**Key facts:**\n{facts}\n\n"
                      f"**System answer:**\n\n{row['answer']}\n\n**Cited passages:**\n\n{cited}\n")
    DIR.mkdir(parents=True, exist_ok=True)
    (DIR / "sheet.md").write_text("\n".join(blocks), encoding="utf-8", newline="\n")
    (DIR / "sample.jsonl").write_text("".join(json.dumps(s) + "\n" for s in sample), encoding="utf-8", newline="\n")
    print(f"{len(sample)} answers to grade -> {DIR / 'sheet.md'} (judge labels kept apart in sample.jsonl)")


def score(grader: str) -> None:
    sheet = (DIR / "sheet.md").read_text(encoding="utf-8")
    grades = {}
    for block in re.split(r"^## (?=J-\d+)", sheet, flags=re.M)[1:]:
        grade = re.search(r"^grade:[ \t]*(\S*)", block, flags=re.M)
        notes = re.search(r"^notes:[ \t]*(.*)$", block, flags=re.M)
        grades[block.split()[0]] = (grade.group(1).lower() if grade else "", notes.group(1).strip() if notes else "")
    sample = [json.loads(line) for line in (DIR / "sample.jsonl").read_text(encoding="utf-8").splitlines()]
    missing = [s["sample_id"] for s in sample if grades.get(s["sample_id"], ("",))[0] not in LABELS]
    if missing:
        raise SystemExit(f"grade must be one of {LABELS}; missing or invalid for: {', '.join(missing)}")

    df = pd.DataFrame([{**s, "human": grades[s["sample_id"]][0], "notes": grades[s["sample_id"]][1]} for s in sample])
    agreement = float((df["human"] == df["judge_correctness"]).mean())
    confusion = pd.crosstab(df["human"], df["judge_correctness"]).reindex(index=LABELS, columns=LABELS, fill_value=0)
    passed = agreement >= THRESHOLD
    result = {"agreement": round(agreement, 4), "threshold": THRESHOLD, "passed": passed, "n": len(df),
              "grader": grader, "graded_on": date.today().isoformat(), "judge_model": get_settings().judge_model,
              "judge_prompt_version": JUDGE_PROMPT_VERSION, "confusion_human_x_judge": confusion.to_dict(),
              "disagreements": df[df["human"] != df["judge_correctness"]][
                  ["sample_id", "item_id", "config", "human", "judge_correctness", "notes"]].to_dict("records")}
    (DIR / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8", newline="\n")
    print(f"agreement {agreement:.0%} (threshold {THRESHOLD:.0%}) -> {'PASSED' if passed else 'FAILED'}")
    print(confusion.to_string())
    log_mlflow(result)


def log_mlflow(result: dict) -> None:
    import mlflow

    from src.tracking import git_state, init_tracking
    init_tracking()
    commit, dirty = git_state()
    with mlflow.start_run(run_name="judge validation"):
        mlflow.set_tags({"run_type": "judge_validation", "git_commit": commit, "git_dirty": str(dirty),
                         "validation_status": "passed" if result["passed"] else "failed",
                         "graded_by": result["grader"], "graded_on": result["graded_on"]})
        mlflow.log_params({"judge_model": result["judge_model"], "judge_prompt_version": result["judge_prompt_version"],
                           "sample_size": result["n"], "threshold": result["threshold"], "seed": SEED})
        mlflow.log_metric("agreement", result["agreement"])
        mlflow.log_artifacts(str(DIR), "judge_validation")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "sheet":
        make_sheet()
    elif command == "score":
        score(grader=sys.argv[2] if len(sys.argv) > 2 else "Ivan Namor")
    else:
        raise SystemExit(__doc__.split("Usage")[1])
