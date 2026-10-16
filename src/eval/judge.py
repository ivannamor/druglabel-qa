"""LLM-as-judge (Claude Haiku 5.5, another vendor than the generator) for what needs judgment:

- correctness: which key facts of the expected answer the answer states, and whether it contradicts it;
- faithfulness: for each factual claim in the answer, whether the passage it cites supports it.

What can be computed is computed, not judged: refusals, invalid citations and false refusals are
decided in `src/eval/run.py`. Verdicts are cached on disk (re-runs are free and identical) and every
call is a Langfuse generation with its cost. The judge is trusted only after its verdicts agree with
human grades on a sample above a threshold fixed in advance (see `src/eval/validate_judge.py`).
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Literal

import anthropic
from pydantic import BaseModel

from src.generation.llm import cost_usd
from src.settings import get_settings
from src.tracing import langfuse, observe

CACHE_DIR = Path("data/cache/judge")
JUDGE_PROMPT_VERSION = "judge_v1"


class Claim(BaseModel):
    claim: str
    supported: bool  # the cited passage states it (not just related)


class Verdict(BaseModel):
    key_facts_present: list[bool]  # one per expected key fact, in order
    contradicts_expected: bool  # the answer states something incompatible with the expected answer
    claims: list[Claim]  # every factual claim of the answer, checked against its cited passages
    explanation: str  # one or two sentences


PROMPT = """You grade an answer from a drug-label question-answering system. Be strict and literal.

Question: {question}

Expected answer: {expected_answer}
Key facts (in order):
{key_facts}

System answer (citations in square brackets are passage IDs):
{answer}

Cited passages:
{passages}

1. key_facts_present: for each key fact, true if the system answer states it (wording may differ).
2. contradicts_expected: true if the system answer says something incompatible with the expected answer.
3. claims: split the system answer into its factual claims; for each, supported = true only if a passage
   it cites states that claim. A claim with no citation is unsupported.
4. explanation: one or two sentences."""


@observe(name="judge", as_type="generation", capture_input=False, capture_output=False)
def judge(question: str, expected_answer: str, key_facts: list[str], answer: str,
          cited_passages: dict[str, str]) -> Verdict:
    s = get_settings()
    prompt = PROMPT.format(
        question=question, expected_answer=expected_answer, answer=answer,
        key_facts="\n".join(f"{i}. {f}" for i, f in enumerate(key_facts, 1)) or "(none)",
        passages="\n\n".join(f"[{cid}]\n{text}" for cid, text in cited_passages.items()) or "(none)")
    key = hashlib.sha256(json.dumps([s.judge_model, prompt]).encode()).hexdigest()
    cached = CACHE_DIR / f"{key}.json"
    if cached.exists():
        langfuse().update_current_generation(model=s.judge_model, input=prompt, metadata={"cached": True},
                                             cost_details={"total": 0.0})
        return Verdict.model_validate_json(cached.read_text(encoding="utf-8"))

    client = anthropic.Anthropic(api_key=s.anthropic_api_key.get_secret_value(), max_retries=5)
    start = time.time()
    r = client.messages.parse(model=s.judge_model, max_tokens=16000,
                              messages=[{"role": "user", "content": prompt}], output_format=Verdict)
    if r.stop_reason == "refusal" or r.parsed_output is None:
        raise RuntimeError(f"judge declined or returned no verdict (stop_reason={r.stop_reason})")
    verdict = r.parsed_output
    langfuse().update_current_generation(
        model=s.judge_model, input=prompt, output=verdict.model_dump(),
        usage_details={"input": r.usage.input_tokens, "output": r.usage.output_tokens},
        cost_details={"total": cost_usd(s.judge_model, r.usage.input_tokens, r.usage.output_tokens) or 0.0},
        metadata={"latency_s": round(time.time() - start, 2), "prompt_version": JUDGE_PROMPT_VERSION})
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cached.write_text(verdict.model_dump_json(), encoding="utf-8")
    return verdict


def correctness(verdict: Verdict) -> Literal["correct", "partial", "incorrect"]:
    """correct = every key fact present and no contradiction; partial = some facts, no contradiction."""
    if verdict.contradicts_expected or not any(verdict.key_facts_present):
        return "incorrect"
    return "correct" if all(verdict.key_facts_present) else "partial"


def faithfulness(verdict: Verdict) -> float | None:
    """Share of the answer's claims supported by their cited passage (None if no claims)."""
    return sum(c.supported for c in verdict.claims) / len(verdict.claims) if verdict.claims else None
