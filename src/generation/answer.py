"""Answer a question from the drug labels: retrieve passages, ask the LLM, check the citations.

The prompt is a versioned file (prompts/<name>.md); its name and sha256 are returned with every answer,
so a logged run identifies the exact instructions used. Citations are parsed from the answer and
checked against the passages that were actually retrieved: a citation to anything else is invalid.

Usage (from repo root): python -m src.generation.answer "What is the antidote for dabigatran?"
"""

import hashlib
import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Literal

import pandas as pd

from src.generation.llm import LLMResponse, complete
from src.retrieval.graph import GraphFact
from src.retrieval.hybrid import retrieve
from src.retrieval.vector import RetrievedChunk
from src.settings import get_settings

CHUNK_ID = re.compile(r"[0-9a-f-]{36}:[a-z_]+:\d+")
Status = Literal["answered", "not_in_labels", "patient_specific", "uncited"]


@dataclass(frozen=True)
class Answer:
    question: str
    text: str
    status: Status  # "uncited": an answer with no valid citation, never to be returned as final
    citations: list[str]  # valid: cited and retrieved, in order of first appearance
    invalid_citations: list[str]  # cited but not among the retrieved passages
    retrieved: list[RetrievedChunk]
    graph_facts: list[GraphFact]  # edges behind the graph passages (graph and hybrid modes)
    retrieval_mode: str
    prompt_name: str
    prompt_sha256: str
    llm: LLMResponse


def load_prompt(name: str) -> tuple[str, str]:
    """Prompt template and the sha256 of its exact content."""
    content = Path(f"prompts/{name}.md").read_text(encoding="utf-8")
    return content, hashlib.sha256(content.encode()).hexdigest()


@lru_cache
def label_routes() -> dict[str, str]:
    """label_id -> route of administration, so the LLM can tell products of one drug apart."""
    meta = pd.read_parquet(get_settings().label_metadata_path, columns=["label_id", "route"])
    return dict(zip(meta["label_id"], meta["route"]))


def format_passages(chunks: list[RetrievedChunk]) -> str:
    def date(yyyymmdd: str) -> str:
        return f"{yyyymmdd[:4]}-{yyyymmdd[4:6]}-{yyyymmdd[6:]}"
    return "\n\n".join(
        f"[{c.chunk_id}] {c.drug} · {c.section.replace('_', ' ')}"
        f"{' · ' + c.subsection if c.subsection else ''} "
        f"(route {label_routes().get(c.label_id, 'unknown').lower()}, label effective {date(c.effective_time)})"
        f"\n{c.text}"
        for c in chunks
    )


def parse_citations(text: str, retrieved_ids: set[str]) -> tuple[list[str], list[str]]:
    """(valid, invalid) chunk IDs cited inside square brackets, deduplicated in order."""
    cited = list(dict.fromkeys(cid for group in re.findall(r"\[([^\[\]]+)\]", text) for cid in CHUNK_ID.findall(group)))
    return [c for c in cited if c in retrieved_ids], [c for c in cited if c not in retrieved_ids]


def answer(question: str) -> Answer:
    s = get_settings()
    retrieved, facts = retrieve(question)
    template, prompt_sha = load_prompt(s.answer_prompt)
    prompt = template.replace("{passages}", format_passages(retrieved)).replace("{question}", question)
    llm = complete(prompt, s.llm_provider, s.llm_model, s.llm_fallback_model, s.llm_temperature)

    valid, invalid = parse_citations(llm.text, {c.chunk_id for c in retrieved})
    if llm.text == "NOT_IN_LABELS":
        status: Status = "not_in_labels"
    elif llm.text == "PATIENT_SPECIFIC":
        status = "patient_specific"
    else:
        status = "answered" if valid else "uncited"
    return Answer(question, llm.text, status, valid, invalid, retrieved, facts, s.retrieval_mode,
                  s.answer_prompt, prompt_sha, llm)


if __name__ == "__main__":
    a = answer(" ".join(sys.argv[1:]) or "What is the antidote for dabigatran?")
    print(f"{a.text}\n")
    print(f"status: {a.status} | valid citations: {len(a.citations)} | invalid: {a.invalid_citations or 'none'}")
    print(f"model: {a.llm.model} | tokens in/out: {a.llm.input_tokens}/{a.llm.output_tokens} | {a.llm.latency_s}s "
          f"| prompt {a.prompt_name} ({a.prompt_sha256[:12]})")
