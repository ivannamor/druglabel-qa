"""LLM client: one `complete()` for OpenAI, Azure OpenAI, Anthropic and Gemini (Google AI Studio).

The provider is a settings value, so switching to Azure is one line in `.env`. OpenAI-style providers go
through the `openai` SDK; Anthropic through its official `anthropic` SDK. Transient errors (rate limits,
overload, 5xx) are retried with backoff, then an optional fallback model is tried. The response records
which model actually answered, so a run never claims a model it did not use.

Batch jobs (graph extraction, evaluation) pass `cache=True`: a response is stored on disk under the hash
of (provider, model, temperature, prompt, json mode), so re-running a job costs nothing and returns the
same answers. Calls are spaced by `llm_min_interval_s` to stay under the providers' requests per minute.
"""

import hashlib
import json
import re
import time
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path

import anthropic
import openai

from src.settings import LLMProvider, get_settings

RETRYABLE = (openai.InternalServerError, openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError,
             anthropic.InternalServerError, anthropic.RateLimitError, anthropic.APITimeoutError,
             anthropic.APIConnectionError)
THOUGHT = re.compile(r"<thought>.*?(?:</thought>|$)\s*", re.S)  # Gemma's reasoning, also if cut off
CACHE_DIR = Path("data/cache/llm")
_last_call = 0.0  # time of the previous API call in this process, for request spacing


@dataclass(frozen=True)
class LLMResponse:
    text: str  # the answer, without any <thought> block
    model: str  # model that actually answered (the fallback if the primary failed)
    input_tokens: int
    output_tokens: int
    latency_s: float


class LLMError(RuntimeError):
    """All attempts on the primary and the fallback model failed."""


@lru_cache
def get_client(provider: LLMProvider) -> openai.OpenAI | anthropic.Anthropic:
    s = get_settings()
    if provider == "openai":
        return openai.OpenAI(api_key=s.openai_api_key.get_secret_value(), timeout=120, max_retries=0)
    if provider == "anthropic":
        return anthropic.Anthropic(api_key=s.anthropic_api_key.get_secret_value(), timeout=120, max_retries=0)
    if provider == "azure_openai":
        return openai.AzureOpenAI(azure_endpoint=s.azure_openai_endpoint, api_version=s.azure_openai_api_version,
                                  api_key=s.azure_openai_api_key.get_secret_value(), timeout=120, max_retries=0)
    if provider == "gemini":
        return openai.OpenAI(base_url=s.gemini_base_url, api_key=s.gemini_api_key.get_secret_value(),
                             timeout=120, max_retries=0)
    raise NotImplementedError(f"provider {provider!r} has no client")


def _call(provider: LLMProvider, model: str, prompt: str, temperature: float, json_mode: bool) -> tuple[str, int, int]:
    """One API call: (text, input tokens, output tokens)."""
    client = get_client(provider)
    if provider == "anthropic":
        if json_mode:
            raise NotImplementedError("JSON mode for Anthropic: use structured outputs (output_config.format)")
        # No temperature: current Claude models reject non-default sampling parameters.
        r = client.messages.create(model=model, max_tokens=16000, messages=[{"role": "user", "content": prompt}])
        text = "".join(b.text for b in r.content if b.type == "text")
        return text, r.usage.input_tokens, r.usage.output_tokens
    extra = {"response_format": {"type": "json_object"}} if json_mode else {}
    r = client.chat.completions.create(model=model, temperature=temperature,
                                       messages=[{"role": "user", "content": prompt}], **extra)
    return r.choices[0].message.content or "", r.usage.prompt_tokens, r.usage.completion_tokens


def complete(prompt: str, provider: LLMProvider, model: str, fallback_model: str | None = None,
             temperature: float = 0.0, attempts: int = 5, json_mode: bool = False,
             cache: bool = False) -> LLMResponse:
    """Send one user message; retry transient errors with backoff, then try the fallback model."""
    key = hashlib.sha256(json.dumps([provider, model, temperature, json_mode, prompt]).encode()).hexdigest()
    cached = CACHE_DIR / f"{key}.json"
    if cache and cached.exists():
        return LLMResponse(**json.loads(cached.read_text(encoding="utf-8")))

    global _last_call
    errors = []
    for m in [model] + ([fallback_model] if fallback_model else []):
        for attempt in range(attempts):
            time.sleep(max(0.0, _last_call + get_settings().llm_min_interval_s - time.time()))
            start = _last_call = time.time()
            try:
                text, tokens_in, tokens_out = _call(provider, m, prompt, temperature, json_mode)
            except RETRYABLE as e:
                errors.append(f"{m}: {type(e).__name__}")
                time.sleep(min(60, 5 * 2 ** attempt))  # 5, 10, 20, 40, 60 s: overload spikes last a while
                continue
            response = LLMResponse(THOUGHT.sub("", text).strip(), m, tokens_in, tokens_out,
                                   round(time.time() - start, 2))
            if cache:
                CACHE_DIR.mkdir(parents=True, exist_ok=True)
                cached.write_text(json.dumps(asdict(response)), encoding="utf-8")
            return response
    raise LLMError("; ".join(errors))
