"""LLM client: one OpenAI-compatible interface for Gemini (Google AI Studio), Azure OpenAI and OpenAI.

The provider is a settings value, so switching to Azure is one line in `.env`. Free tiers fail often
(HTTP 500/503, rate limits), so calls retry with backoff and then try a fallback model. The response
records which model actually answered, so a run never claims a model it did not use.
"""

import re
import time
from dataclasses import dataclass
from functools import lru_cache

from openai import (APIConnectionError, APITimeoutError, AzureOpenAI, InternalServerError, OpenAI,
                    RateLimitError)

from src.settings import LLMProvider, get_settings

RETRYABLE = (InternalServerError, RateLimitError, APITimeoutError, APIConnectionError)
THOUGHT = re.compile(r"<thought>.*?(?:</thought>|$)\s*", re.S)  # Gemma's reasoning, also if cut off


@dataclass(frozen=True)
class LLMResponse:
    text: str  # the answer, without the model's <thought> block
    model: str  # model that actually answered (the fallback if the primary failed)
    input_tokens: int
    output_tokens: int
    latency_s: float


class LLMError(RuntimeError):
    """All attempts on the primary and the fallback model failed."""


@lru_cache
def get_client(provider: LLMProvider) -> OpenAI:
    s = get_settings()
    if provider == "gemini":
        return OpenAI(base_url=s.gemini_base_url, api_key=s.gemini_api_key.get_secret_value(), timeout=120, max_retries=0)
    if provider == "azure_openai":
        return AzureOpenAI(azure_endpoint=s.azure_openai_endpoint, api_key=s.azure_openai_api_key.get_secret_value(),
                           api_version=s.azure_openai_api_version, timeout=120, max_retries=0)
    if provider == "openai":
        return OpenAI(api_key=s.openai_api_key.get_secret_value(), timeout=120, max_retries=0)
    raise NotImplementedError(f"provider {provider!r} has no client yet")


def complete(prompt: str, provider: LLMProvider, model: str, fallback_model: str | None = None,
             temperature: float = 0.0, attempts: int = 3) -> LLMResponse:
    """Send one user message; retry transient errors with backoff, then try the fallback model."""
    client = get_client(provider)
    errors = []
    for m in [model] + ([fallback_model] if fallback_model else []):
        for attempt in range(attempts):
            start = time.time()
            try:
                r = client.chat.completions.create(model=m, temperature=temperature,
                                                   messages=[{"role": "user", "content": prompt}])
            except RETRYABLE as e:
                errors.append(f"{m}: {type(e).__name__}")
                time.sleep(2 * 2 ** attempt)  # 2, 4, 8 s
                continue
            return LLMResponse(
                text=THOUGHT.sub("", r.choices[0].message.content or "").strip(),
                model=m,
                input_tokens=r.usage.prompt_tokens,
                output_tokens=r.usage.completion_tokens,
                latency_s=round(time.time() - start, 2),
            )
    raise LLMError("; ".join(errors))
