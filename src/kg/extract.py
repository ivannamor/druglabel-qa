"""Extract knowledge-graph relations from drug label sections with an LLM.

One representative label per (drug, route): products of one drug can differ in use (dipyridamole tablets
are an antiplatelet, the injection a diagnostic agent), while generic labels copy the brand label, so
the other labels of a route would mostly repeat the same facts at several times the LLM calls. Preference:
modern format (PLR), then the reference product's label (NDA application), then the most recent one.
Every relation keeps the route and label it comes from. One LLM call per (label, section); each relation must name the chunk it comes from and quote
it. The quote must appear verbatim in one of the passages sent: if it is in a different passage than the one
cited, the relation is attributed to the passage that actually contains it (`chunk_id_corrected`); if it is
in none, the relation is rejected. Rejected relations are kept with the reason, not silently dropped.

Usage (from repo root):
    python -m src.kg.extract --drugs apixaban,warfarin   # trial on a few drugs, no MLflow run
    python -m src.kg.extract --log                        # all drugs, logged as an MLflow run
"""

import argparse
import json
import re
import uuid
from pathlib import Path

import pandas as pd

from src.generation.answer import format_passages, load_prompt
from src.generation.llm import LLMError, complete
from src.kg.normalize import brand_map, normalize
from src.retrieval.vector import RetrievedChunk
from src.settings import get_settings

# section -> (relation type, allowed target types, what to extract)
SECTIONS = {
    "indications_and_usage": ("INDICATED_FOR", ["Condition"],
        "the diseases or conditions the drug is indicated to treat or prevent"),
    "contraindications": ("CONTRAINDICATED_IN", ["Condition"],
        "the patient conditions in which the drug is contraindicated (not drug combinations)"),
    "adverse_reactions": ("HAS_ADVERSE_REACTION", ["AdverseEvent"],
        "adverse reactions of the drug; at most 40, preferring those described as serious or most common"),
    "drug_interactions": ("INTERACTS_WITH", ["Drug", "DrugClass"],
        "the drugs or drug classes that interact with the drug (a named drug is Drug; a group such as "
        "'strong cyp3a4 inhibitor' or 'nsaid' is DrugClass)"),
    "precautions": ("INTERACTS_WITH", ["Drug", "DrugClass"],  # old-format labels: interactions sit here
        "only the drugs or drug classes that interact with the drug (ignore all other precautions; a named "
        "drug is Drug, a group is DrugClass)"),
}
OUT_DIR = Path("data/kg")


def representative_labels(gold: pd.DataFrame, meta: pd.DataFrame) -> pd.DataFrame:
    labels = (gold.drop_duplicates("label_id")[["label_id", "drug", "label_format", "effective_time"]]
              .merge(meta[["label_id", "route", "application_number"]], on="label_id"))
    labels = labels.assign(plr=labels["label_format"].eq("PLR"),
                           nda=labels["application_number"].fillna("").str.startswith("NDA"))
    return (labels.sort_values(["plr", "nda", "effective_time", "label_id"], ascending=False)
            .drop_duplicates(["drug", "route"]))


def squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def extract_section(chunks: pd.DataFrame, drug: str, route: str, section: str, brands: dict[str, str],
                    template: str) -> tuple[list[dict], list[dict], dict]:
    """(accepted, rejected, llm usage) for one section of one label."""
    relation, target_types, instruction = SECTIONS[section]
    passages = [RetrievedChunk(r.chunk_id, r.label_id, r.effective_time, r.drug, r.section,
                               r.subsection if isinstance(r.subsection, str) else None, r.text, 0.0, 1)
                for r in chunks.itertuples()]
    prompt = (template.replace("{drug}", drug).replace("{section}", section.replace("_", " "))
              .replace("{instruction}", instruction).replace("{target_types}", ", ".join(target_types))
              .replace("{passages}", format_passages(passages)))
    s = get_settings()
    try:
        llm = complete(prompt, s.llm_provider, s.llm_model, temperature=0.0, json_mode=True, cache=True)
    except LLMError as e:  # recorded and skipped; a re-run retries only these sections (the rest is cached)
        return [], [{"drug": drug, "section": section, "reason": "llm_error", "raw": str(e)}], {"model": None}
    usage = {"model": llm.model, "input_tokens": llm.input_tokens, "output_tokens": llm.output_tokens}

    try:
        items = json.loads(llm.text).get("relations", [])
    except (json.JSONDecodeError, AttributeError):
        return [], [{"drug": drug, "section": section, "reason": "invalid_json", "raw": llm.text[:500]}], usage

    text_by_id = dict(zip(chunks["chunk_id"], chunks["text"].map(squash)))
    accepted, rejected, seen = [], [], set()
    for item in items:
        target_type = item.get("target_type")
        target = normalize(str(item.get("target", "")), brands if target_type == "Drug" else None)
        quote = squash(str(item.get("evidence") or ""))
        cited = item.get("chunk_id")
        found = [cid for cid, text in text_by_id.items() if quote and quote in text]
        source = cited if cited in found else (found[0] if len(found) == 1 else None)
        row = {"drug": drug, "route": route, "relation": relation, "target": target, "target_type": target_type,
               "source_chunk_id": source or cited, "chunk_id_corrected": bool(source and source != cited),
               "label_id": chunks["label_id"].iloc[0], "evidence": item.get("evidence"), "section": section}
        if not target or target_type not in target_types:
            reason = "bad_target"
        elif source is None:
            reason = "evidence_not_in_passages" if not found else "evidence_ambiguous"
        elif (relation, target) in seen:
            reason = "duplicate"
        else:
            seen.add((relation, target))
            accepted.append(row)
            continue
        rejected.append({**row, "reason": reason})
    return accepted, rejected, usage


def run_extraction(drugs: list[str] | None) -> dict:
    s = get_settings()
    gold = pd.read_parquet(s.gold_snapshot_path, columns=[
        "chunk_id", "label_id", "effective_time", "label_format", "drug", "brand_names",
        "section", "subsection", "chunk_index", "text", "gold_delta_version"])
    brands = brand_map(gold.groupby("drug")["brand_names"]
                       .apply(lambda b: sorted({x for s in b.dropna() for x in s.split("; ") if x})).to_dict())
    reps = representative_labels(gold, pd.read_parquet(s.label_metadata_path))
    if drugs:
        reps = reps[reps["drug"].isin(drugs)]
    template, prompt_sha = load_prompt("extract_v1")

    accepted, rejected, calls = [], [], []
    for rep in reps.itertuples():
        label = gold[gold["label_id"] == rep.label_id].sort_values(["section", "chunk_index"])
        for section in SECTIONS:
            chunks = label[label["section"] == section]
            if chunks.empty:
                continue
            ok, bad, usage = extract_section(chunks, rep.drug, rep.route, section, brands, template)
            accepted += ok
            rejected += bad
            calls.append({"drug": rep.drug, "route": rep.route, "section": section, **usage,
                          "accepted": len(ok), "rejected": len(bad)})
            print(f"{rep.drug:<22} {rep.route[:14]:<14} {section:<22} accepted {len(ok):>3}  rejected {len(bad):>2}",
                  flush=True)
    return {"accepted": accepted, "rejected": rejected, "calls": calls, "labels": reps,
            "prompt_sha256": prompt_sha, "gold_version": int(gold["gold_delta_version"].iloc[0])}


def save(result: dict, run_id: str) -> Path:
    out = OUT_DIR / f"extraction_{run_id}"
    out.mkdir(parents=True, exist_ok=True)
    for name in ("accepted", "rejected", "calls"):
        rows = [{**r, "extraction_run_id": run_id} for r in result[name]] if name == "accepted" else result[name]
        (out / f"{name}.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    result["labels"].to_csv(out / "labels.csv", index=False)
    return out


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--drugs", help="comma-separated dataset drug names (default: all)")
    parser.add_argument("--log", action="store_true", help="log the extraction as an MLflow run")
    args = parser.parse_args()
    drugs = [d.strip() for d in args.drugs.split(",")] if args.drugs else None

    if args.log:
        import mlflow

        from src.tracking import config_params, git_state, init_tracking
        init_tracking()
        commit, dirty = git_state()
        with mlflow.start_run(run_name="kg extraction") as run:
            run_id = run.info.run_id  # extraction_run_id on every edge = this MLflow run
            result = run_extraction(drugs)
            out = save(result, run_id)
            reasons = pd.Series([r["reason"] for r in result["rejected"]]).value_counts().to_dict()
            mlflow.set_tags({"run_type": "kg_extraction", "git_commit": commit, "git_dirty": str(dirty)})
            mlflow.log_params({**config_params(), "prompt_name": "extract_v1",
                               "prompt_sha256": result["prompt_sha256"], "labels": len(result["labels"])})
            mlflow.log_metrics({"llm_calls": len(result["calls"]), "accepted": len(result["accepted"]),
                                "rejected": len(result["rejected"]),
                                **{f"rejected_{k}": v for k, v in reasons.items()},
                                **{f"relations_{k}": v for k, v in pd.Series(
                                    [r["relation"] for r in result["accepted"]]).value_counts().items()}})
            mlflow.log_artifacts(str(out), "extraction")
            mlflow.log_text(load_prompt("extract_v1")[0], "prompts/extract_v1.md")
    else:
        run_id = f"trial-{uuid.uuid4().hex[:8]}"
        result = run_extraction(drugs)
        out = save(result, run_id)

    n_ok, n_bad = len(result["accepted"]), len(result["rejected"])
    print(f"\n{n_ok} relations accepted, {n_bad} rejected ({n_bad / max(1, n_ok + n_bad):.0%}) "
          f"| {len(result['calls'])} LLM calls | run {run_id} | files in {out}")
