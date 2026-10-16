"""Graph retrieval: find the label passages behind the knowledge-graph edges a question is about.

1. Entity linking: graph node names (drugs, drug classes, conditions, adverse events) and brand names
   found in the question (both sides normalized alike); role words ("anticoagulants", "antiplatelet
   drugs") become a filter on drugs. A linked drug class also brings in the classes that contain all its
   words: "strong cyp3a inhibitor" -> "combined p-gp and strong cyp3a inhibitor".
2. Relation hint from keywords ("interact" -> INTERACTS_WITH, ...); none found = all relation types.
3. Cypher query for edges touching the linked entities, ranked by how many of them an edge matches.
4. The edges' `source_chunk_id`s are returned as passages, so answers cite label text exactly as with
   vector retrieval, and multi-hop questions ("which anticoagulants interact with amiodarone?") get the
   passages spread over several labels.

Usage (from repo root): python -m src.retrieval.graph "Which anticoagulants interact with amiodarone?"
"""

import re
import sys
from dataclasses import dataclass
from functools import lru_cache

import pandas as pd

from src.kg.graph_db import get_driver
from src.kg.normalize import brand_map, normalize_text
from src.retrieval.vector import RetrievedChunk
from src.settings import get_settings

RELATION_HINTS = {
    "INTERACTS_WITH": r"interact|co-?administ|concomitant|taken with|combined with|together with",
    "CONTRAINDICATED_IN": r"contraindicat|must not|should not be used",
    "INDICATED_FOR": r"indicat|used for|used to treat|approved for|treat",
    "HAS_ADVERSE_REACTION": r"adverse|side effect|reaction|cause",
}
ROLE_WORDS = {
    "anticoagulant": r"anticoagulants?",
    "antiplatelet": r"antiplatelets?|antiplatelet (?:drugs?|agents?)",
    "thrombolytic": r"thrombolytics?",
    "reversal": r"reversal agents?|antidotes?",
}


@dataclass(frozen=True)
class GraphFact:
    drug: str
    relation: str
    target: str
    route: str
    source_chunk_id: str
    evidence: str


@lru_cache
def entity_names() -> dict[str, str]:
    """Lowercase surface form -> graph node name: all node names plus brand names of dataset drugs."""
    s = get_settings()
    records, _, _ = get_driver().execute_query("MATCH (n) RETURN n.name AS name", database_=s.neo4j_database)
    names = {r["name"]: r["name"] for r in records if r["name"] and len(r["name"]) >= 4}  # skip "pe"-like names
    gold = pd.read_parquet(s.gold_snapshot_path, columns=["drug", "brand_names"])
    brands = brand_map(gold.groupby("drug")["brand_names"]
                       .apply(lambda b: sorted({x for v in b.dropna() for x in v.split("; ") if x})).to_dict())
    names.update({b: d for b, d in brands.items() if len(b) >= 4})
    return names


@lru_cache
def class_words() -> dict[str, frozenset[str]]:
    """DrugClass node name -> its words in singular form, for containment matching."""
    records, _, _ = get_driver().execute_query("MATCH (c:DrugClass) RETURN c.name AS name",
                                               database_=get_settings().neo4j_database)
    return {r["name"]: words(r["name"]) for r in records}


def words(name: str) -> frozenset[str]:
    return frozenset(w[:-1] if len(w) > 3 and w.endswith("s") else w for w in re.findall(r"[a-z0-9-]+", name))


@lru_cache
def chunk_table() -> pd.DataFrame:
    s = get_settings()
    return pd.read_parquet(s.gold_snapshot_path, columns=[
        "chunk_id", "label_id", "effective_time", "drug", "section", "subsection", "text"]).set_index("chunk_id")


def link(question: str) -> tuple[list[str], list[str], list[str]]:
    """(graph node names, relation types, drug roles) mentioned in the question."""
    q = normalize_text(question)
    found, taken = [], []
    for surface in sorted(entity_names(), key=len, reverse=True):  # longest first: "strong cyp3a4 inhibitor"
        for m in re.finditer(rf"\b{re.escape(surface)}s?\b", q):
            if not any(a <= m.start() < b for a, b in taken):  # not inside a longer name already found
                taken.append((m.start(), m.end()))
                found.append(entity_names()[surface])
    classes = class_words()
    found += [c for name in found if name in classes for c, w in classes.items() if classes[name] < w]
    relations = [rel for rel, pattern in RELATION_HINTS.items() if re.search(pattern, q)]
    roles = [role for role, pattern in ROLE_WORDS.items() if re.search(rf"\b(?:{pattern})\b", q)]
    return list(dict.fromkeys(found)), relations, roles


def search(question: str, max_passages: int) -> tuple[list[RetrievedChunk], list[GraphFact]]:
    names, relations, roles = link(question)
    if not names and not roles:
        return [], []
    records, _, _ = get_driver().execute_query(
        """MATCH (d:Drug)-[e]->(t)
           WHERE (size($relations) = 0 OR type(e) IN $relations)
             AND (d.name IN $names OR t.name IN $names OR (size($names) = 0 AND d.role IN $roles))
             AND (size($roles) = 0 OR d.role IN $roles OR t.role IN $roles)
           WITH d, e, t, toInteger(d.name IN $names) + toInteger(t.name IN $names)
                + toInteger(d.role IN $roles OR t.role IN $roles) AS matched
           RETURN d.name AS drug, type(e) AS relation, t.name AS target, e.route AS route,
                  e.source_chunk_id AS chunk_id, e.evidence AS evidence, matched
           ORDER BY matched DESC, drug, relation, target LIMIT 200""",
        names=names, relations=relations, roles=roles, database_=get_settings().neo4j_database)
    facts = [GraphFact(r["drug"], r["relation"], r["target"], r["route"], r["chunk_id"], r["evidence"])
             for r in records]

    chunks, best = chunk_table(), {}
    for r in records:  # one passage per source chunk, scored by its best-matching edge
        best[r["chunk_id"]] = max(best.get(r["chunk_id"], 0), r["matched"])
    top = sorted(best, key=lambda cid: -best[cid])[:max_passages]
    top_matched = max(best.values())
    passages = []
    for cid in top:
        c = chunks.loc[cid]
        passages.append(RetrievedChunk(cid, c.label_id, c.effective_time, c.drug, c.section,
                                       c.subsection if isinstance(c.subsection, str) else None, c.text,
                                       score=best[cid] / top_matched, n_labels=1))
    return passages, facts


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "Which anticoagulants interact with amiodarone?"
    print("linked:", link(question))
    passages, facts = search(question, get_settings().graph_max_passages)
    print(f"{len(facts)} graph facts, {len(passages)} passages\n")
    for f in facts[:15]:
        print(f"  ({f.drug}) -[{f.relation} {f.route}]-> ({f.target})  [{f.source_chunk_id[:8]}…]")
    for p in passages:
        print(f"\n{p.score:.2f} {p.chunk_id}  [{p.drug} · {p.section}]\n   {p.text[:150]}…")
