"""Entity name normalization for the knowledge graph: simple rules, no external ontology.

Lowercase, collapse whitespace, strip punctuation and leading articles, a small synonym table, and
brand names mapped to the generic names used in the dataset (so "Plavix" and "clopidogrel" are one node).
"""

import re

SYNONYMS = {
    "hemorrhage": "bleeding",
    "haemorrhage": "bleeding",
    "bleeding event": "bleeding",
    "nsaid": "nonsteroidal anti-inflammatory drug",
    "nsaids": "nonsteroidal anti-inflammatory drug",
    "non-steroidal anti-inflammatory drug": "nonsteroidal anti-inflammatory drug",
    "ssri": "selective serotonin reuptake inhibitor",
    "snri": "serotonin norepinephrine reuptake inhibitor",
    "acetylsalicylic acid": "aspirin",
    "dvt": "deep vein thrombosis",
    "pe": "pulmonary embolism",
}


# Well-known US brands whose brand label is not among the selected labels (only generics were); the rest
# of the brand map is built from the `brand_names` of the dataset.
KNOWN_BRANDS = {
    "plavix": "clopidogrel",
    "coumadin": "warfarin",
    "jantoven": "warfarin",
    "pradaxa": "dabigatran etexilate",
    "dabigatran": "dabigatran etexilate",
    "brilinta": "ticagrelor",
    "pletal": "cilostazol",
    "persantine": "dipyridamole",
    "cordarone": "amiodarone",
    "pacerone": "amiodarone",
    "lipitor": "atorvastatin",
    "lanoxin": "digoxin",
}


def brand_map(drug_brands: dict[str, list[str]]) -> dict[str, str]:
    """Lowercase brand (and salt) names → dataset generic name, e.g. 'xarelto' → 'rivaroxaban'."""
    mapping = dict(KNOWN_BRANDS)
    for drug, brands in drug_brands.items():
        for b in brands:
            mapping.setdefault(re.sub(r"\s+", " ", b).strip().lower(), drug)
    return mapping


def normalize(name: str, brand_to_generic: dict[str, str] | None = None) -> str:
    n = re.sub(r"\s+", " ", name).strip().lower()
    n = re.sub(r"^(the|a|an) ", "", n).strip(" .,;:")
    n = SYNONYMS.get(n, n)
    # "severe hypersensitivity reaction to eliquis" -> "hypersensitivity": one node across drugs
    if re.match(r"^(known |severe |serious )*hypersensitivity( reaction)?s?( to .*)?$", n):
        n = "hypersensitivity"
    return (brand_to_generic or {}).get(n, n)
