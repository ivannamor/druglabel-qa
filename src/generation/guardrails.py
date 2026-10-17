"""Guardrails: decide whether an answer is released or held for human review. All checks are computed
(no LLM), explainable, and recorded with the answer.

Refusals (NOT_IN_LABELS, PATIENT_SPECIFIC) are released: refusing is the safe outcome. An answer is held
for review if any of these holds:
- no_valid_citation: it cites no retrieved passage;
- invalid_citation: it cites something that was not retrieved (or a passage number that does not exist);
- low_grounding: a sentence's content words are poorly covered by the passages it cites (lexical proxy
  for "every claim is supported by its cited passage"; threshold calibrated against the LLM judge);
- wrong_drug: the question names specific dataset drugs, but the answer cites another drug's label;
- multi_drug: the answer draws on the labels of two or more drugs (multi-hop answers are the weakest
  and least consistent in evaluation: they are always reviewed);
- patient_specific_wording: the question reads like a single-patient decision but was answered anyway
  (backup for the generator's PATIENT_SPECIFIC refusal).
"""

import re
from dataclasses import dataclass, field
from functools import lru_cache

from src.generation.answer import Answer
from src.retrieval.graph import chunk_table, link
from src.retrieval.vector import RetrievedChunk
from src.settings import get_settings

STOPWORDS = frozenset("""a an and are as at be been being but by can could did do does for from had has have how if in
into is it its may might more most must no not of on or other should such than that the their them then there these
they this those to under use used using was were what when where which while who will with would also any each
including patients patient label labeling drug drugs dose""".split())
PATIENT_WORDING = re.compile(
    r"\b(?:my|our|this) patient\b|\b\d{1,3}[- ]year[- ]old\b|\bweigh(?:s|ing)? \d+|\b\d+(?:\.\d+)? ?kg\b"
    r"|\bshould (?:i|we) (?:give|prescribe|start|stop|switch|use)\b|\bwhat dose should\b", re.I)
SENTENCE = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9(])")
CITATION = re.compile(r"\[([0-9a-f-]{36}:[a-z_]+:\d+)\]")


@dataclass(frozen=True)
class GuardrailResult:
    released: bool
    reasons: list[str] = field(default_factory=list)
    grounding: float | None = None  # lowest sentence grounding score, 0..1 (None for refusals)
    cited_drugs: list[str] = field(default_factory=list)


@lru_cache
def dataset_drugs() -> frozenset[str]:
    return frozenset(chunk_table()["drug"].unique())


def words(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-z0-9][a-z0-9.%-]*", text.lower()) if w not in STOPWORDS and len(w) > 2}


def grounding(answer_text: str, passages: dict[str, str]) -> float:
    """Lowest, over the answer's sentences, share of a sentence's content words found in the passages it
    cites. A sentence that cites nothing scores 0; very short sentences (fewer than 3 content words) are
    skipped because one word decides their score."""
    scores = []
    for sentence in SENTENCE.split(answer_text):
        content = words(CITATION.sub("", sentence))
        if len(content) < 3:
            continue
        cited = [passages[c] for c in CITATION.findall(sentence) if c in passages]
        source = set().union(*(words(p) for p in cited)) if cited else set()
        scores.append(len(content & source) / len(content))
    return min(scores) if scores else 0.0


def check(question: str, a: Answer, min_grounding: float | None = None) -> GuardrailResult:
    if a.status in ("not_in_labels", "patient_specific"):
        return GuardrailResult(released=True)
    threshold = get_settings().min_grounding if min_grounding is None else min_grounding
    by_id: dict[str, RetrievedChunk] = {c.chunk_id: c for c in a.retrieved}
    cited_drugs = sorted({by_id[c].drug for c in a.citations if c in by_id})
    reasons = []
    if not a.citations:
        reasons.append("no_valid_citation")
    if a.invalid_citations:
        reasons.append("invalid_citation")
    score = grounding(a.text, {c: by_id[c].text for c in a.citations if c in by_id})
    if score < threshold:
        reasons.append("low_grounding")
    named = {n for n in link(question)[0] if n in dataset_drugs()}  # brand names already mapped to generics
    if len(named) == 1 and any(d not in named for d in cited_drugs):  # a question about one drug
        reasons.append("wrong_drug")
    if len(cited_drugs) >= 2:
        reasons.append("multi_drug")
    if PATIENT_WORDING.search(question):
        reasons.append("patient_specific_wording")
    return GuardrailResult(released=not reasons, reasons=reasons, grounding=round(score, 3), cited_drugs=cited_drugs)
