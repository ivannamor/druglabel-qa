"""Release gate: execute the test protocol, write the traceability matrix, approve or reject the release.

Runs every test case of validation/test_protocol.md against the committed code, compares results with the
approved criteria in validation/acceptance_criteria.json, logs one MLflow validation run, and writes
validation/traceability_matrix.csv (requirement -> test -> MLflow run -> result -> status). Only if every
test passes are the approval tags set (`validation_status=approved`, `approved_by`, `approval_date`) on the
validation run and on the TC-01 evaluation run; otherwise the release is marked rejected.

Usage (from repo root): python -m src.validation.release --approver "Ivan Namor"
"""

import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import date
from pathlib import Path

import mlflow
import pandas as pd

from src.ask import ask
from src.eval.run import OUT_DIR, load_items, run_config
from src.generation.hitl import _client, _sql, table
from src.tracing import langfuse
from src.tracking import git_state, init_tracking

VALIDATION = Path("validation")
CRITERIA = json.loads((VALIDATION / "acceptance_criteria.json").read_text(encoding="utf-8"))
REQUIREMENTS = {  # test -> requirements it verifies (test_protocol.md)
    "TC-01": ["REQ-01", "REQ-02", "REQ-04", "REQ-05", "REQ-06", "REQ-08", "REQ-09"],
    "TC-02": ["REQ-02", "REQ-03"], "TC-03": ["REQ-01", "REQ-07"], "TC-04": ["REQ-07"], "TC-05": ["REQ-05"],
    "TC-06": ["REQ-10"], "TC-07": ["REQ-07"], "TC-08": ["REQ-09"], "TC-09": ["REQ-03", "REQ-15"],
    "TC-10": ["REQ-11"], "TC-11": ["REQ-12"], "TC-12": ["REQ-14"], "TC-13": ["REQ-13"], "TC-14": ["REQ-15"],
}
PYTEST_CASES = {  # test -> pytest functions
    "TC-02": ["test_citation_to_unretrieved_passage_is_invalid",
              "test_passage_numbers_map_to_chunk_ids_and_unknown_numbers_are_invalid"],
    "TC-03": ["test_grounded_sentence_scores_high_and_uncited_sentence_scores_zero", "test_unsupported_claim_scores_low"],
    "TC-04": ["test_supported_single_drug_answer_is_released", "test_answer_without_citation_is_held",
              "test_invalid_citation_is_held", "test_citing_another_drugs_label_for_a_single_drug_question_is_held",
              "test_multi_drug_answer_is_held", "test_refusals_are_released"],
    "TC-05": ["test_patient_specific_wording"],
    "TC-06": ["test_instructions_inside_a_passage_are_not_followed"],
    "TC-08": ["test_normalization_merges_brand_synonym_and_enzyme_variants"],
    "TC-09": ["test_every_chunk_traces_back_to_its_label_version"],
}
MULTI_DRUG_QUESTION = "Which drugs in the dataset interact with strong CYP3A4 inhibitors?"


def meets(value, rule: list) -> bool:
    op, threshold = rule
    return value is not None and (value >= threshold if op == ">=" else value <= threshold)


def pytest_results(out_dir: Path) -> dict[str, bool]:
    """Run unit and integration tests; return pass/fail per test function."""
    xml = out_dir / "pytest.xml"
    subprocess.run([sys.executable, "-m", "pytest", "-q", "-o", "addopts=", f"--junitxml={xml}"], check=False)
    outcome = {}
    for case in ET.parse(xml).getroot().iter("testcase"):
        outcome[case.get("name")] = not any(child.tag in ("failure", "error", "skipped") for child in case)
    return outcome


def main(approver: str) -> None:
    commit, dirty = git_state()
    if dirty:
        raise SystemExit("Uncommitted changes: the validation run must execute committed code.")
    out_dir = OUT_DIR / "validation"
    out_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict] = {}

    # TC-02..06, TC-08, TC-09: automated tests
    outcome = pytest_results(out_dir)
    for tc, names in PYTEST_CASES.items():
        missing = [n for n in names if n not in outcome]
        passed = not missing and all(outcome[n] for n in names)
        results[tc] = {"passed": passed, "detail": f"{sum(outcome.get(n, False) for n in names)}/{len(names)} tests passed"
                       + (f"; missing {missing}" if missing else "")}

    # TC-01: golden-set evaluation of the release configuration
    conf = CRITERIA["release_configuration"]
    summary = run_config(load_items(None), conf["retrieval_mode"], conf["answer_prompt"], conf["repeats"],
                         log=True, run_type="validation_tc01")
    tc01_run = summary["mlflow_run_id"]
    failed = {m: summary.get(m) for m, rule in CRITERIA["TC-01"].items() if not meets(summary.get(m), rule)}
    results["TC-01"] = {"passed": not failed, "mlflow_run_id": tc01_run,
                        "detail": "; ".join(f"{m}={summary.get(m)} ({' '.join(map(str, r))})"
                                            for m, r in CRITERIA["TC-01"].items())}

    # TC-07: a multi-drug answer goes to the review queue, not to the user
    a, guard, review_id, trace_id = ask(MULTI_DRUG_QUESTION)
    langfuse().flush()
    row = None
    if review_id:
        w, warehouse = _client()
        r = _sql(w, warehouse, f"SELECT status, reasons, citations, prompt_sha256, git_commit, trace_id FROM {table()} "
                               f"WHERE review_id = '{review_id}'")
        row = (r.result.data_array or [None])[0] if r.result else None
    results["TC-07"] = {"passed": bool(not guard.released and row and row[0] == "pending" and all(row[1:])),
                        "detail": f"released={guard.released} reasons={guard.reasons} review_id={review_id}"}

    # TC-10: reproducibility record of the TC-01 run
    run = mlflow.get_run(tc01_run)
    p, tags = run.data.params, run.data.tags
    needed = ["prompt_name", "prompt_sha256", "gold_delta_version", "silver_delta_version", "gold_snapshot_sha256",
              "golden_set_sha256", "llm_model", "models_used", "embedding_model", "retrieval_mode", "top_k"]
    absent = [k for k in needed if not p.get(k)]
    results["TC-10"] = {"passed": not absent and tags.get("git_dirty") == "False" and tags.get("git_commit") == commit,
                        "detail": f"commit {tags.get('git_commit', '')[:7]}, dirty={tags.get('git_dirty')}, missing={absent}"}

    # TC-11: tracing — a trace for every evaluated answer; generations carry tokens and cost
    tc01 = pd.read_json(OUT_DIR / f"{conf['retrieval_mode']}_{conf['answer_prompt']}_r{conf['repeats']}" / "results.jsonl",
                        lines=True)
    def generations(tid: str) -> list:
        return langfuse().api.observations.get_many(trace_id=tid, type="GENERATION", fields="core,basic,usage,model").data
    sampled = generations(tc01["trace_id"].iloc[0])
    live = generations(trace_id) if trace_id else []
    has = lambda gens: any(g.usage_details and g.cost_details is not None for g in gens)  # noqa: E731
    results["TC-11"] = {"passed": bool(tc01["trace_id"].notna().all() and has(sampled) and has(live)
                                       and any((g.total_cost or 0) > 0 for g in live)),
                        "detail": f"{int(tc01['trace_id'].notna().sum())}/{len(tc01)} answers traced; sampled "
                                  f"generations {len(sampled)}, live generations {len(live)}"}

    # TC-12: judge validation (blind human grades)
    jv = json.loads((OUT_DIR / "judge_validation" / "result.json").read_text(encoding="utf-8"))
    jv_runs = mlflow.search_runs(filter_string="tags.run_type = 'judge_validation'", order_by=["start_time DESC"],
                                 max_results=1, search_all_experiments=True)
    results["TC-12"] = {"passed": meets(jv["agreement"], CRITERIA["TC-12"]["agreement"]),
                        "mlflow_run_id": jv_runs["run_id"].iloc[0] if len(jv_runs) else None,
                        "detail": f"agreement {jv['agreement']} on {jv['n']} answers, graded by {jv['grader']}"}

    # TC-14: raw data preserved
    w, warehouse = _client()
    r = _sql(w, warehouse, "DESCRIBE HISTORY workspace.druglabel_qa.bronze_labels")
    history = r.result.data_array if r.result else []
    results["TC-14"] = {"passed": len(history) == 1 and str(history[0][0]) == "0",
                        "detail": f"{len(history)} version(s) of bronze_labels: "
                                  + ", ".join(f"v{h[0]} {h[4]}" for h in history)}

    # TC-13: release gate, then the validation run with every result
    all_passed = all(r["passed"] for r in results.values())
    results["TC-13"] = {"passed": True, "detail": "approval set" if all_passed else "release rejected: approval withheld"}
    init_tracking()
    status = "approved" if all_passed else "rejected"
    approval = {"validation_status": status, "approved_by": approver if all_passed else "",
                "approval_date": date.today().isoformat() if all_passed else ""}
    with mlflow.start_run(run_name="release validation v1.0.0") as vrun:
        validation_run = vrun.info.run_id
        mlflow.set_tags({"run_type": "release_validation", "git_commit": commit, "git_dirty": "False",
                         "release": "v1.0.0", "tc01_run_id": tc01_run, **approval})
        mlflow.log_params({"acceptance_criteria_version": CRITERIA["version"], **{f"{tc}_passed": str(v["passed"])
                                                                                   for tc, v in results.items()}})
        mlflow.log_metric("tests_passed", sum(r["passed"] for r in results.values()))
        mlflow.log_metric("tests_total", len(results))
        matrix = [{"req_id": req, "test_id": tc,
                   "mlflow_run_id": results[tc].get("mlflow_run_id") or validation_run,
                   "result": results[tc]["detail"], "status": "pass" if results[tc]["passed"] else "fail"}
                  for tc in sorted(REQUIREMENTS) for req in REQUIREMENTS[tc]]
        pd.DataFrame(sorted(matrix, key=lambda m: (m["req_id"], m["test_id"]))).to_csv(
            VALIDATION / "traceability_matrix.csv", index=False, lineterminator="\n")
        mlflow.log_dict(results, "validation/results.json")
        for f in ("acceptance_criteria.json", "traceability_matrix.csv"):
            mlflow.log_artifact(str(VALIDATION / f), "validation")
        mlflow.log_artifact(str(out_dir / "pytest.xml"), "validation")
    if all_passed:
        for key in ("validation_status", "approved_by", "approval_date"):
            mlflow.MlflowClient().set_tag(tc01_run, key, approval[key])

    (out_dir / "results.json").write_text(json.dumps({"release": "v1.0.0", "git_commit": commit, "status": status,
                                                      "validation_run": validation_run, "tc01_run": tc01_run,
                                                      **approval, "results": results}, indent=2),
                                          encoding="utf-8", newline="\n")
    for tc in sorted(results):
        print(f"{tc}  {'PASS' if results[tc]['passed'] else 'FAIL'}  {results[tc]['detail'][:150]}")
    print(f"\nRelease v1.0.0: {status.upper()} | validation run {validation_run} | TC-01 run {tc01_run}")
    if not all_passed:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--approver", required=True)
    main(parser.parse_args().approver)
