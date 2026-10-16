"""Golden set: LLM-drafted questions, reviewed and approved by a human before use.

Drafting uses a third model (Claude Sonnet 5.5), neither the generator nor the judge, so the questions
do not inherit either model's wording. Every item records its source passages and the drafting model;
every approved item records reviewer and date (ALCOA+ "attributable").

- single_fact: one question per sampled passage (representative labels, stratified by section).
- multi_hop: questions whose answer spans several labels ("which anticoagulants interact with X?").
  Candidate drugs come from the knowledge graph AND from a keyword search of the label text, so a fact
  the graph extraction missed can still be in the expected answer; the drafter keeps only the drugs
  whose passages support the claim.
- unanswerable: drugs outside the dataset, information labels do not contain, patient-specific dosing.

Usage (from repo root):
    python -m src.eval.golden draft      # -> data/golden/draft.jsonl and data/golden/review.csv
    python -m src.eval.golden sheet      # rebuild review.csv from the draft, keeping decisions already made
    python -m src.eval.golden import     # review.csv decisions -> data/golden_set.jsonl
    python -m src.eval.golden paraphrase # reworded copies of approved questions -> paraphrases_draft.jsonl
    python -m src.eval.golden add-paraphrases GS-P01,GS-P02   # approved paraphrases -> golden set
"""

import csv
import io
import json
import random
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path
from typing import Literal

import anthropic
import pandas as pd
from pydantic import BaseModel

from src.kg.extract import representative_labels
from src.kg.graph_db import get_driver
from src.kg.normalize import normalize_text
from src.settings import get_settings

DRAFTER = "claude-sonnet-5-5"
GOLDEN_DIR = Path("data/golden")
SEED = 20261017
SINGLE_FACT_SECTIONS = {  # section group -> number of passages to sample
    "indications": 3, "contraindications": 3, "dosage": 4, "warnings": 4, "adverse_reactions": 3,
    "interactions": 3, "specific_populations": 3, "pharmacology": 2, "product": 2, "overdosage": 1,
}
OUT_OF_DATASET = ["metformin", "lisinopril", "sertraline", "levothyroxine", "amoxicillin", "insulin glargine"]
ROLE_PLURAL = {"anticoagulant": "anticoagulants", "antiplatelet": "antiplatelet drugs", None: "drugs"}


class SingleFact(BaseModel):
    suitable: bool  # false if the passage has no fact worth asking about (e.g., only a table header)
    question: str
    expected_answer: str
    key_facts: list[str]


class MultiHop(BaseModel):
    question: str
    qualifying_drugs: list[str]  # candidate drugs whose passages support the claim
    expected_answer: str
    key_facts: list[str]  # one per qualifying drug
    supporting_chunk_ids: list[str]


class Unanswerable(BaseModel):
    questions: list[str]


def ask(prompt: str, schema: type[BaseModel]) -> BaseModel | None:
    """One structured call to the drafter; None if it declines (counted, not retried on another model)."""
    client = anthropic.Anthropic(api_key=get_settings().anthropic_api_key.get_secret_value())
    r = client.messages.parse(model=DRAFTER, max_tokens=16000, output_config={"effort": "medium"},
                              messages=[{"role": "user", "content": prompt}], output_format=schema)
    return None if r.stop_reason == "refusal" else r.parsed_output


STYLE = ("Write as a pharmacist or physician would ask a medical information service: natural wording, not "
         "copied from the passage, naming the drug (generic or brand) and, if it matters, the formulation.")


def load_corpus() -> tuple[pd.DataFrame, pd.DataFrame]:
    """(chunks of the representative labels, representative labels with route and role)."""
    s = get_settings()
    gold = pd.read_parquet(s.gold_snapshot_path, columns=[
        "chunk_id", "label_id", "effective_time", "label_format", "drug", "role", "section", "section_group",
        "subsection", "text"])
    reps = representative_labels(gold, pd.read_parquet(s.label_metadata_path))
    reps = reps.merge(gold.drop_duplicates("drug")[["drug", "role"]], on="drug")
    return gold[gold["label_id"].isin(reps["label_id"])].merge(reps[["label_id", "route"]], on="label_id"), reps


def draft_single_fact(chunks: pd.DataFrame, rng: random.Random) -> list[dict]:
    items, used_drugs = [], set()
    for group, n in SINGLE_FACT_SECTIONS.items():
        pool = chunks[(chunks["section_group"] == group) & (chunks["text"].str.len() > 300)]
        candidates = pool.sample(frac=1, random_state=rng.randint(0, 10**6)).itertuples()
        picked = 0
        for c in candidates:  # prefer drugs not used yet, so the set covers many labels
            if picked == n:
                break
            if c.drug in used_drugs and len(used_drugs) < chunks["drug"].nunique():
                continue
            out = ask(f"""Write one question whose answer is stated in this FDA label passage, and its answer.
{STYLE}
The answer must come only from the passage. Give the expected answer in 1-3 sentences and list its key facts
(each a short checkable statement). If the passage contains nothing worth asking, set suitable to false.

Drug: {c.drug} ({c.route.lower()}) · section: {c.section.replace('_', ' ')}
Passage:
{c.text}""", SingleFact)
            if out is None or not out.suitable:
                continue
            used_drugs.add(c.drug)
            picked += 1
            items.append({"type": "single_fact", "question": out.question, "expected_behavior": "answer",
                          "expected_answer": out.expected_answer, "key_facts": out.key_facts,
                          "gold_chunk_ids": [c.chunk_id], "drugs": [c.drug],
                          "source": f"passage {c.chunk_id}"})
            print(f"single_fact  {c.drug:<22} {group}", flush=True)
    return items


def multi_hop_specs(chunks: pd.DataFrame) -> list[dict]:
    """Questions answerable only by combining labels: drugs (of a role) linked to one shared target."""
    s = get_settings()
    records, _, _ = get_driver().execute_query(
        """MATCH (d:Drug {in_dataset: true})-[e]->(t)
           WHERE type(e) IN ['INTERACTS_WITH', 'CONTRAINDICATED_IN']
           RETURN type(e) AS relation, t.name AS target, d.role AS role, collect(DISTINCT d.name) AS drugs""",
        database_=s.neo4j_database)
    specs = []
    for r in records:  # targets that at least two drugs share in the graph; the keyword search may add more
        if len(r["drugs"]) >= 2:
            specs += [{"relation": r["relation"], "target": r["target"], "role": role}
                      for role in ([r["role"]] if r["role"] in ROLE_PLURAL else []) + [None]]
    # keep targets that at least two drugs share (by graph or by text), then pick a varied subset
    out, seen = [], set()
    for spec in specs:
        key = (spec["relation"], spec["target"], spec["role"])
        if key in seen:
            continue
        seen.add(key)
        cands = candidates(chunks, spec)
        if 2 <= len(cands) <= 6:
            out.append({**spec, "candidates": cands})
    return out


def candidates(chunks: pd.DataFrame, spec: dict) -> dict[str, list[str]]:
    """Drug -> chunk IDs that may support the claim: graph edges plus a keyword search of the text."""
    s = get_settings()
    sections = (["drug_interactions", "precautions", "warnings_and_cautions", "clinical_pharmacology"]
                if spec["relation"] == "INTERACTS_WITH" else ["contraindications"])
    records, _, _ = get_driver().execute_query(
        f"MATCH (d:Drug)-[e:{spec['relation']}]->(t {{name: $target}}) "
        "WHERE $role IS NULL OR d.role = $role RETURN d.name AS drug, e.source_chunk_id AS chunk_id",
        target=spec["target"], role=spec["role"], database_=s.neo4j_database)
    found = defaultdict(set)
    for r in records:
        found[r["drug"]].add(r["chunk_id"])
    pattern = r"\b" + r"\s+".join(map(re.escape, spec["target"].split())) + r"s?\b"
    pool = chunks[chunks["section"].isin(sections)]
    if spec["role"]:
        pool = pool[pool["role"] == spec["role"]]
    for c in pool.itertuples():
        if c.drug != spec["target"] and re.search(pattern, normalize_text(c.text)):
            found[c.drug].add(c.chunk_id)
    return {d: sorted(ids) for d, ids in found.items() if d != spec["target"]}


def draft_multi_hop(chunks: pd.DataFrame, rng: random.Random, n: int = 22) -> list[dict]:
    specs = multi_hop_specs(chunks)
    rng.shuffle(specs)
    by_relation = defaultdict(list)
    for spec in specs:
        by_relation[spec["relation"]].append(spec)
    picked = by_relation["INTERACTS_WITH"][: n * 2 // 3] + by_relation["CONTRAINDICATED_IN"][: n - n * 2 // 3]
    text = chunks.set_index("chunk_id")["text"]
    items = []
    for spec in picked:
        group = ROLE_PLURAL.get(spec["role"], "drugs")
        claim = ("interacts with" if spec["relation"] == "INTERACTS_WITH" else "is contraindicated in")
        evidence = "\n\n".join(f"[{cid}] {drug}:\n{text[cid]}" for drug, ids in spec["candidates"].items()
                               for cid in ids[:2])
        out = ask(f"""Candidate {group} that may say the drug {claim} "{spec['target']}", with passages from
their FDA labels. Keep only the candidates whose passages clearly support it. Then write one question
asking which {group} in the dataset {claim.replace('is ', 'are ').replace('interacts', 'interact')}
"{spec['target']}". {STYLE}
Give the expected answer naming every qualifying drug (with what its label says, in a few words), one key
fact per qualifying drug, and the IDs of the passages that support them.

Candidates: {', '.join(spec['candidates'])}
Passages:
{evidence}""", MultiHop)
        if out is None or len(out.qualifying_drugs) < 2:
            continue
        items.append({"type": "multi_hop", "question": out.question, "expected_behavior": "answer",
                      "expected_answer": out.expected_answer, "key_facts": out.key_facts,
                      "gold_chunk_ids": [c for c in out.supporting_chunk_ids if c in text.index],
                      "drugs": out.qualifying_drugs,
                      "source": f"graph+keyword: {spec['relation']} {spec['target']} ({group})"})
        print(f"multi_hop    {spec['relation']:<19} {spec['target'][:40]:<40} {len(out.qualifying_drugs)} drugs",
              flush=True)
    return items


def draft_unanswerable(reps: pd.DataFrame) -> list[dict]:
    drugs = ", ".join(sorted(reps["drug"].unique()))
    asks = {
        "not_in_labels": (f"Write 6 questions a clinician might ask a medical information service that an FDA "
                          f"drug label cannot answer: 3 about drugs NOT in this list ({', '.join(OUT_OF_DATASET)}), "
                          f"and 3 about drugs in this list ({drugs}) but on topics labels do not cover (price, "
                          f"availability in a specific country, comparisons of brands, policy). {STYLE}"),
        "patient_specific": (f"Write 5 questions asking what to do for one specific patient (age, weight, kidney "
                             f"function or other details given) with a drug from this list: {drugs}. Each must ask "
                             f"for an individual treatment or dose decision, not the label's general "
                             f"recommendation. {STYLE}"),
    }
    items = []
    for behavior, prompt in asks.items():
        out = ask(prompt, Unanswerable)
        for q in (out.questions if out else []):
            items.append({"type": "unanswerable", "question": q, "expected_behavior": behavior,
                          "expected_answer": "NOT_IN_LABELS" if behavior == "not_in_labels" else "PATIENT_SPECIFIC",
                          "key_facts": [], "gold_chunk_ids": [], "drugs": [], "source": f"drafted ({behavior})"})
        print(f"unanswerable {behavior:<19} {len(out.questions) if out else 0}", flush=True)
    return items


def draft() -> None:
    rng = random.Random(SEED)
    chunks, reps = load_corpus()
    items = draft_single_fact(chunks, rng) + draft_multi_hop(chunks, rng) + draft_unanswerable(reps)
    for i, item in enumerate(items, 1):
        item.update({"id": f"GS-{i:03d}", "drafted_by": DRAFTER, "drafted_on": date.today().isoformat()})
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    (GOLDEN_DIR / "draft.jsonl").write_text("".join(json.dumps(i) + "\n" for i in items), encoding="utf-8")

    write_review_sheet(items, chunks)
    counts = pd.Series([i["type"] for i in items]).value_counts().to_dict()
    print(f"\n{len(items)} drafted items {counts} -> {GOLDEN_DIR / "draft.jsonl"}, review sheet {REVIEW_FILE}")


REVIEW_FILE = GOLDEN_DIR / "review.csv"
REVIEW_FIELDS = ["decision", "edited_question", "edited_expected_answer", "notes"]  # filled in by the reviewer


def read_review_sheet() -> list[dict]:
    """Rows of review.csv, whatever an editor saved it as: UTF-8 with or without BOM or the Windows code
    page; comma, semicolon or tab separated."""
    raw = REVIEW_FILE.read_bytes()
    try:
        content = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        content = raw.decode("cp1252")
    delimiter = csv.Sniffer().sniff(content.splitlines()[0], delimiters=",;\t").delimiter
    return list(csv.DictReader(io.StringIO(content), delimiter=delimiter))


def write_review_sheet(items: list[dict], chunks: pd.DataFrame) -> None:
    """Standard CSV (comma, UTF-8) with every gold passage in full; decisions already made are kept."""
    kept = {r["id"]: r for r in read_review_sheet()} if REVIEW_FILE.exists() else {}
    text = chunks.set_index("chunk_id")["text"]
    with open(REVIEW_FILE, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["id", "type", "expected_behavior", "question", "expected_answer", "key_facts",
                    "source_passages"] + REVIEW_FIELDS)
        for i in items:
            passages = "\n---\n".join(f"[{cid}]\n{text[cid]}" for cid in i["gold_chunk_ids"])
            previous = kept.get(i["id"], {})
            w.writerow([i["id"], i["type"], i["expected_behavior"], i["question"], i["expected_answer"],
                        "\n".join(i["key_facts"]), passages] + [previous.get(c, "") for c in REVIEW_FIELDS])


class Paraphrase(BaseModel):
    question: str


def draft_paraphrases(n_single: int = 10, n_multi: int = 5) -> None:
    """Reworded versions of approved questions (robustness); they inherit the reviewed expected answer."""
    golden = [json.loads(line) for line in Path("data/golden_set.jsonl").read_text(encoding="utf-8").splitlines()]
    rng = random.Random(SEED)
    picked = (rng.sample([i for i in golden if i["type"] == "single_fact"], n_single)
              + rng.sample([i for i in golden if i["type"] == "multi_hop"], n_multi))
    out = []
    for k, item in enumerate(picked, 1):
        p = ask(f"""Reword this question so it asks exactly the same thing with different words and sentence
structure, as another healthcare professional might phrase it. Keep every detail that changes the answer
(drug, formulation, population). Do not add or drop anything.

Question: {item['question']}""", Paraphrase)
        if p is None:
            continue
        out.append({**item, "id": f"GS-P{k:02d}", "question": p.question, "paraphrase_of": item["id"],
                    "drafted_by": DRAFTER, "drafted_on": date.today().isoformat()})
        print(f"GS-P{k:02d} <- {item['id']}", flush=True)
    (GOLDEN_DIR / "paraphrases_draft.jsonl").write_text("".join(json.dumps(i) + "\n" for i in out), encoding="utf-8")


def add_paraphrases(ids: list[str], reviewer: str) -> None:
    """Append the approved paraphrases to the golden set, with reviewer and date."""
    drafts = {i["id"]: i for i in map(json.loads, (GOLDEN_DIR / "paraphrases_draft.jsonl").read_text(
        encoding="utf-8").splitlines())}
    golden_path = Path("data/golden_set.jsonl")
    golden = [json.loads(line) for line in golden_path.read_text(encoding="utf-8").splitlines()]
    golden = [i for i in golden if i["id"] not in drafts]  # re-running replaces earlier paraphrases
    golden += [{**drafts[i], "review": "approve", "reviewed_by": reviewer, "reviewed_on": date.today().isoformat(),
                "review_notes": ""} for i in ids]
    golden_path.write_text("".join(json.dumps(i) + "\n" for i in golden), encoding="utf-8")
    print(f"{len(ids)} paraphrases added; golden set: {len(golden)} items")


def import_review(reviewer: str) -> None:
    drafts = {i["id"]: i for i in map(json.loads, (GOLDEN_DIR / "draft.jsonl").read_text(encoding="utf-8").splitlines())}
    approved = []
    for row in (r for r in read_review_sheet() if r.get("id")):  # editors may append empty rows
        decision = row["decision"].strip().lower()
        if decision not in ("approve", "edit"):
            continue
        item = dict(drafts[row["id"]])
        if decision == "edit":
            item["question"] = row["edited_question"].strip() or item["question"]
            item["expected_answer"] = row["edited_expected_answer"].strip() or item["expected_answer"]
        item.update({"review": decision, "reviewed_by": reviewer, "reviewed_on": date.today().isoformat(),
                     "review_notes": row["notes"].strip()})
        approved.append(item)
    Path("data/golden_set.jsonl").write_text("".join(json.dumps(i) + "\n" for i in approved), encoding="utf-8")
    print(f"{len(approved)} approved items -> data/golden_set.jsonl",
          pd.Series([i["type"] for i in approved]).value_counts().to_dict())


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "draft":
        draft()
    elif command == "sheet":
        write_review_sheet([json.loads(line) for line in (GOLDEN_DIR / "draft.jsonl").read_text(
            encoding="utf-8").splitlines()], pd.read_parquet(get_settings().gold_snapshot_path, columns=["chunk_id", "text"]))
        print(f"review sheet rebuilt: {REVIEW_FILE}")
    elif command == "import":
        import_review(reviewer=sys.argv[2] if len(sys.argv) > 2 else "Ivan Namor")
    elif command == "paraphrase":
        draft_paraphrases()
    elif command == "add-paraphrases":  # add-paraphrases GS-P01,GS-P02 "Reviewer Name"
        add_paraphrases(sys.argv[2].split(","), reviewer=sys.argv[3] if len(sys.argv) > 3 else "Ivan Namor")
    else:
        raise SystemExit(__doc__.split("Usage")[1])
