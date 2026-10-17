"""Unit tests for the computed safeguards: citation checks, guardrail routing and entity normalization.

They run offline on synthetic answers (no LLM calls); the graph-based entity linking needs Neo4j and the
Gold snapshot, like the application. Test IDs (TC-xx) refer to validation/test_protocol.md.
Run from the repo root: python -m pytest -q
"""

from src.generation.answer import Answer, numbers_to_chunk_ids, parse_citations
from src.generation.guardrails import PATIENT_WORDING, check, grounding
from src.generation.llm import LLMResponse
from src.kg.normalize import normalize
from src.retrieval.vector import RetrievedChunk

APIXABAN = "35ab1342-e927-4bd0-9020-628b859dfb38:contraindications:1"
WARFARIN = "5a5b5d79-6112-f2ac-e063-6394a90a2244:contraindications:1"
TEXT = ("ELIQUIS is contraindicated in patients with the following conditions: active pathological bleeding "
        "and severe hypersensitivity reaction to ELIQUIS (e.g., anaphylactic reactions).")


def chunk(cid: str, drug: str, text: str = TEXT) -> RetrievedChunk:
    return RetrievedChunk(cid, cid.split(":")[0], "20260424", drug, "contraindications", None, text, 0.8, 1)


def answer(question: str, text: str, retrieved: list[RetrievedChunk], status: str = "answered") -> Answer:
    valid, invalid = parse_citations(text, {c.chunk_id for c in retrieved})
    return Answer(question, text, status, valid, invalid, retrieved, [], "hybrid", "answer_v2", "sha",
                  LLMResponse(text, "test", 0, 0, 0.0))


# TC-02: citations must point to retrieved passages
def test_citation_to_unretrieved_passage_is_invalid():
    valid, invalid = parse_citations(f"Fact [{APIXABAN}]. Other fact [{WARFARIN}].", {APIXABAN})
    assert valid == [APIXABAN] and invalid == [WARFARIN]


def test_passage_numbers_map_to_chunk_ids_and_unknown_numbers_are_invalid():
    text, invalid = numbers_to_chunk_ids("Fact [1]. Other [1, 2]. Bad [7].", [chunk(APIXABAN, "apixaban"),
                                                                           chunk(WARFARIN, "warfarin")])
    assert f"[{APIXABAN}]" in text and f"[{WARFARIN}]" in text and invalid == ["passage 7"]


# TC-03: grounding of each sentence in its cited passage
def test_grounded_sentence_scores_high_and_uncited_sentence_scores_zero():
    passages = {APIXABAN: TEXT}
    assert grounding(f"Eliquis is contraindicated in active pathological bleeding [{APIXABAN}].", passages) > 0.6
    assert grounding("Eliquis is contraindicated in active pathological bleeding.", passages) == 0.0


def test_unsupported_claim_scores_low():
    claim = f"Eliquis requires weekly INR monitoring and liver biopsy before initiation [{APIXABAN}]."
    assert grounding(claim, {APIXABAN: TEXT}) < 0.6


# TC-04: answers that need a human are held
def test_supported_single_drug_answer_is_released():
    a = answer("What are the contraindications of Eliquis?",
               f"Eliquis is contraindicated in active pathological bleeding and severe hypersensitivity [{APIXABAN}].",
               [chunk(APIXABAN, "apixaban")])
    result = check(a.question, a)
    assert result.released, result.reasons


def test_answer_without_citation_is_held():
    a = answer("What are the contraindications of Eliquis?", "Eliquis is contraindicated in bleeding.",
               [chunk(APIXABAN, "apixaban")])
    assert "no_valid_citation" in check(a.question, a).reasons


def test_invalid_citation_is_held():
    a = answer("What are the contraindications of Eliquis?",
               f"Eliquis is contraindicated in active pathological bleeding [{WARFARIN}].", [chunk(APIXABAN, "apixaban")])
    assert "invalid_citation" in check(a.question, a).reasons


def test_citing_another_drugs_label_for_a_single_drug_question_is_held():
    a = answer("What are the contraindications of Eliquis?",
               f"It is contraindicated in active pathological bleeding and hypersensitivity [{WARFARIN}].",
               [chunk(WARFARIN, "warfarin")])
    assert "wrong_drug" in check(a.question, a).reasons


def test_multi_drug_answer_is_held():
    a = answer("Which anticoagulants are contraindicated in active pathological bleeding?",
               f"Eliquis is contraindicated in active pathological bleeding [{APIXABAN}]. Warfarin is "
               f"contraindicated in active pathological bleeding [{WARFARIN}].",
               [chunk(APIXABAN, "apixaban"), chunk(WARFARIN, "warfarin")])
    assert "multi_drug" in check(a.question, a).reasons


def test_refusals_are_released():
    a = answer("What is the maximum dose of metformin?", "NOT_IN_LABELS", [], status="not_in_labels")
    assert check(a.question, a).released


# TC-05: patient-specific wording is recognised as a backup to the model's refusal
def test_patient_specific_wording():
    assert PATIENT_WORDING.search("My patient is 82 years old and weighs 55 kg; what dose of apixaban?")
    assert PATIENT_WORDING.search("Should I give rivaroxaban to this patient?")
    assert not PATIENT_WORDING.search("What is the recommended dose of apixaban in renal impairment?")


# TC-08: one name per entity (wrong-drug confusion)
def test_normalization_merges_brand_synonym_and_enzyme_variants():
    assert normalize("Plavix", {"plavix": "clopidogrel"}) == "clopidogrel"
    assert normalize("Hemorrhage") == "bleeding"
    assert normalize("Strong CYP3A4 inhibitors") == normalize("strong cyp3a inhibitors")
    assert normalize("Severe hypersensitivity reaction to ELIQUIS") == "hypersensitivity"
