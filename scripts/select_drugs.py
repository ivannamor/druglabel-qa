"""Rule-based drug selection: generates data/drug_list.csv from two external sources.

Rules
1. Core = every single-substance drug in WHO ATC group B01A (antithrombotic agents)
   that has at least one single-ingredient prescription label on openFDA.
2. Reversal agents = single substances in ATC V03AB (antidotes) or B02BA (vitamin K)
   whose most recent label's indications mention anticoagulant reversal.
3. Interaction partners = single substances in ATC group C (cardiovascular system, excluding
   C05 vasoprotectives, which are mostly topical) mentioned in the drug_interactions sections of
   at least MIN_CORE_MENTIONS different anticoagulant/antiplatelet core drugs. Modern labels
   often name interacting drugs by mechanism (e.g., "strong CYP3A4 inhibitors"), so the
   threshold is low.
Each selected drug contributes at most MAX_LABELS single-ingredient labels, most recent first.

Outputs (from repo root: python scripts/select_drugs.py)
- data/drug_list.csv                        the selection, with the reason for each drug
- data/exploration/atc_snapshot.csv         ATC codes used, with the WHO index update date
- data/exploration/interaction_mentions.csv how many core drugs mention each ATC C substance
"""

import csv
import re
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests

ATC_URL = "https://atcddd.fhi.no/atc_ddd_index/"
FDA_URL = "https://api.fda.gov/drug/label.json"
MAX_LABELS = 10
MIN_CORE_MENTIONS = 2
PAUSE_S = 0.3

# WHO uses international names (INN); US labels use US names (USAN) for a few substances.
INN_TO_US = {
    "acetylsalicylic acid": "aspirin",
    "phytomenadione": "phytonadione",
    "glyceryl trinitrate": "nitroglycerin",
    "colestyramine": "cholestyramine",
    "andexanet alfa": "andexanet",
}
REVERSAL_KEYWORDS = re.compile(r"anticoagula|heparin|dabigatran|factor xa|warfarin|bleeding", re.I)
# Phrases where a drug name is part of a class name, removed before matching
# ("serotonin norepinephrine reuptake inhibitors" is not a mention of norepinephrine).
FALSE_MENTIONS = re.compile(r"serotonin[- ]norepinephrine reuptake inhibitors?", re.I)
ANTICOAG_ANTIPLATELET = ("B01AA", "B01AB", "B01AC", "B01AE", "B01AF")
ROLE_BY_GROUP = {"B01AA": "anticoagulant", "B01AB": "anticoagulant", "B01AE": "anticoagulant",
                 "B01AF": "anticoagulant", "B01AC": "antiplatelet", "B01AD": "thrombolytic",
                 "B01AX": "other_antithrombotic"}

OUT_LIST = Path("data/drug_list.csv")
OUT_ATC = Path("data/exploration/atc_snapshot.csv")
OUT_MENTIONS = Path("data/exploration/interaction_mentions.csv")


# ---------- WHO ATC ----------

_atc_updated = ""


def atc_page(code: str) -> dict[str, str]:
    """Return {code: name} for every ATC link on the index page of `code` (itself, parents, children)."""
    global _atc_updated
    time.sleep(PAUSE_S)
    html = requests.get(ATC_URL, params={"code": code, "showdescription": "no"}, timeout=60).text
    _atc_updated = _atc_updated or (re.findall(r"\d{4}-\d{2}-\d{2}", html) or [""])[0]
    links = re.findall(r'code=([A-Z0-9]+)&showdescription=no">([^<]+)</a>', html)
    links += re.findall(r'code=([A-Z0-9]{7})&showdescription=yes">([^<]+)</a>', html)
    return {c: n.strip() for c, n in links}


def atc_substances(root: str, exclude: tuple[str, ...] = ()) -> list[dict]:
    """Walk the ATC tree under `root` and return level-5 single substances with their level-4 group.

    A substance listed under several codes is kept once, under its first code.
    """
    found, groups, todo = {}, {}, [root]
    while todo:
        code = todo.pop()
        for child, name in atc_page(code).items():
            if child == code or not child.startswith(code) or child.startswith(exclude):
                groups.setdefault(child, name)
            elif len(child) == 7:
                found[child] = name
            elif child not in groups:
                groups[child] = name
                todo.append(child)
    rows, seen = [], set()
    for code, name in sorted(found.items()):
        is_combination = int(code[5:]) >= 50 or " and " in name or "combination" in name
        us_name = INN_TO_US.get(name, name)
        if not is_combination and us_name not in seen:
            seen.add(us_name)
            rows.append({"atc_code": code, "atc_name": name, "atc_group": code[:5],
                         "atc_group_name": groups.get(code[:5], ""), "us_name": us_name})
    return rows


# ---------- openFDA ----------

_label_cache: dict[str, list[dict]] = {}


def single_ingredient_labels(name: str) -> list[dict]:
    """Single-ingredient Rx labels for a substance, most recent first."""
    if name not in _label_cache:
        time.sleep(PAUSE_S)
        search = f'openfda.generic_name:"{name}" AND openfda.product_type:"HUMAN PRESCRIPTION DRUG"'
        r = requests.get(FDA_URL, params={"search": search, "limit": 1000}, timeout=120)
        results = r.json().get("results", []) if r.ok else []
        single = [x for x in results if len(x.get("openfda", {}).get("substance_name", [])) == 1]
        _label_cache[name] = sorted(single, key=lambda x: x.get("effective_time", ""), reverse=True)
    return _label_cache[name]


def section_text(label: dict, field: str) -> str:
    return " ".join(label.get(field, [])).lower()


# ---------- selection ----------

def main() -> None:
    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    selected: list[dict] = []

    # Rule 1: core antithrombotics
    core = []
    for s in atc_substances("B01A"):
        n = len(single_ingredient_labels(s["us_name"]))
        print(f"core      {s['atc_code']} {s['us_name']:<22} labels={n}")
        if n:
            core.append(s)
            selected.append({**s, "role": ROLE_BY_GROUP.get(s["atc_group"], "other_antithrombotic"),
                             "available_labels": n, "selection_reason": "ATC B01A with Rx label on openFDA"})

    # Rule 2: reversal agents
    reversal_candidates = []
    for root in ("V03AB", "B02BA"):
        for s in atc_substances(root):
            reversal_candidates.append(s)
            labels = single_ingredient_labels(s["us_name"])
            if labels and REVERSAL_KEYWORDS.search(section_text(labels[0], "indications_and_usage")):
                print(f"reversal  {s['atc_code']} {s['us_name']:<22} labels={len(labels)}")
                selected.append({**s, "role": "reversal", "available_labels": len(labels),
                                 "selection_reason": f"ATC {root}; indication mentions anticoagulant reversal"})

    # Rule 3: cardiovascular interaction partners, counted per distinct core drug
    core_names = {c["us_name"] for c in core}
    cv = [s for s in atc_substances("C", exclude=("C05",)) if s["us_name"] not in core_names]
    mentioned_by: dict[str, set[str]] = defaultdict(set)
    for c in core:
        if not c["atc_group"].startswith(ANTICOAG_ANTIPLATELET):
            continue
        text = " ".join(section_text(lb, "drug_interactions")
                        for lb in single_ingredient_labels(c["us_name"])[:MAX_LABELS])
        text = FALSE_MENTIONS.sub(" ", text)
        for s in cv:
            if re.search(rf"\b{re.escape(s['us_name'])}\b", text):
                mentioned_by[s["us_name"]].add(c["us_name"])

    mention_rows = sorted(({"us_name": s["us_name"], "atc_code": s["atc_code"], "atc_group_name": s["atc_group_name"],
                            "core_drugs_mentioning": len(mentioned_by[s["us_name"]]),
                            "mentioned_by": "; ".join(sorted(mentioned_by[s["us_name"]]))}
                           for s in cv if mentioned_by[s["us_name"]]),
                          key=lambda r: -r["core_drugs_mentioning"])
    for s in cv:
        k = len(mentioned_by[s["us_name"]])
        if k >= MIN_CORE_MENTIONS:
            n = len(single_ingredient_labels(s["us_name"]))
            print(f"partner   {s['atc_code']} {s['us_name']:<22} mentioned_by={k} labels={n}")
            if n:
                selected.append({**s, "role": "interaction_partner", "available_labels": n,
                                 "selection_reason": f"ATC C; in drug_interactions of {k} core drugs"})

    # Write outputs
    for row in selected:
        row["max_labels"] = MAX_LABELS
    fields = ["us_name", "atc_code", "atc_name", "atc_group", "atc_group_name", "role",
              "available_labels", "max_labels", "selection_reason"]
    _write(OUT_LIST, selected, fields)
    _write(OUT_MENTIONS, mention_rows, list(mention_rows[0]) if mention_rows else ["us_name"])
    _write(OUT_ATC, [{**s, "who_atc_index_updated": _atc_updated, "retrieved_at": retrieved_at}
                     for s in core + reversal_candidates + cv], None)

    total = sum(min(r["available_labels"], MAX_LABELS) for r in selected)
    print(f"\n{len(selected)} drugs selected, {total} labels at max {MAX_LABELS}/drug "
          f"(WHO ATC index updated {_atc_updated})")


def _write(path: Path, rows: list[dict], fields: list[str] | None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields or list(rows[0]), lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
