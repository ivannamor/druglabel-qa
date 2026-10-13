"""Exploration of the openFDA drug label API: the evidence behind data/drug_list.csv.

For each candidate drug it records how many prescription labels exist, how many are
single-ingredient, and which pharmacologic class FDA reports. Results are written to
data/exploration/label_counts.csv together with the openFDA data date, so the selection
can be re-checked later.

Usage (from repo root):
    python notebooks/00_explore_openfda.py                   # counts -> CSV
    python notebooks/00_explore_openfda.py --example apixaban  # print one label's structure
"""

import argparse
import csv
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

URL = "https://api.fda.gov/drug/label.json"
OUT = Path("data/exploration/label_counts.csv")
PAUSE_S = 0.3  # stay well under the 240 requests/minute limit without an API key

# Candidates considered, including the ones later excluded (see data/drug_list.csv).
CANDIDATES = {
    "anticoagulant": ["warfarin", "apixaban", "rivaroxaban", "dabigatran", "edoxaban", "heparin",
                      "enoxaparin", "dalteparin", "fondaparinux", "argatroban", "bivalirudin"],
    "antiplatelet": ["clopidogrel", "prasugrel", "ticagrelor", "cilostazol", "dipyridamole", "vorapaxar"],
    "reversal": ["idarucizumab", "andexanet", "protamine", "phytonadione"],
    "antiarrhythmic": ["amiodarone", "dronedarone", "digoxin"],
    "other_cv": ["metoprolol", "carvedilol", "diltiazem", "verapamil", "atorvastatin",
                 "simvastatin", "rosuvastatin", "amlodipine", "lisinopril", "sacubitril"],
}


def rx_search(generic: str) -> str:
    return f'openfda.generic_name:"{generic}" AND openfda.product_type:"HUMAN PRESCRIPTION DRUG"'


def get(params: dict) -> dict:
    time.sleep(PAUSE_S)
    r = requests.get(URL, params=params, timeout=60)
    if r.status_code == 404:  # openFDA returns 404 when nothing matches
        return {}
    r.raise_for_status()
    return r.json()


def explore_drug(generic: str) -> dict:
    """Count Rx labels, single-ingredient Rx labels, and FDA classes for one drug."""
    data = get({"search": rx_search(generic), "limit": 1000})  # max page size; enough for every candidate
    results = data.get("results", [])
    total = data.get("meta", {}).get("results", {}).get("total", 0)
    single = sum(1 for x in results if len(x.get("openfda", {}).get("substance_name", [])) == 1)

    classes = get({"search": rx_search(generic), "count": "openfda.pharm_class_epc.exact", "limit": 3})
    class_str = "; ".join(f"{c['term']} ({c['count']})" for c in classes.get("results", []))

    return {"drug": generic, "rx_labels": total, "single_ingredient_labels": single,
            "fda_pharm_class_epc": class_str, "openfda_last_updated": data.get("meta", {}).get("last_updated", "")}


def run_counts() -> None:
    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    rows = []
    for group, drugs in CANDIDATES.items():
        for d in drugs:
            row = {"candidate_group": group, **explore_drug(d), "retrieved_at": retrieved_at}
            rows.append(row)
            print(f"{group:<15} {d:<13} rx={row['rx_labels']:>4} single={row['single_ingredient_labels']:>4}  "
                  f"{row['fda_pharm_class_epc'] or '(no class)'}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nTotal Rx labels: {sum(r['rx_labels'] for r in rows)}  ->  written to {OUT}")


def show_example(generic: str) -> None:
    """Print the IDs, openfda metadata and section fields of one label."""
    x = get({"search": rx_search(generic), "limit": 1})["results"][0]
    print(f"id={x['id']}  set_id={x['set_id']}  version={x.get('version')}  effective_time={x.get('effective_time')}")
    for k in ["brand_name", "generic_name", "manufacturer_name", "product_type", "substance_name", "pharm_class_epc"]:
        print(f"openfda.{k:<18} {x['openfda'].get(k)}")
    print("\nSections:")
    for k, v in x.items():
        if isinstance(v, list) and v and isinstance(v[0], str):
            text = " ".join(v)
            print(f"  {k:<45} {len(text):>6} chars | {text[:70]!r}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--example", metavar="DRUG", help="print the structure of one label instead of counting")
    args = parser.parse_args()
    show_example(args.example) if args.example else run_counts()
