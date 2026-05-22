"""OpenRouter provider.

OpenRouter exposes an OpenAI-compatible API, so this reuses the ``openai``
SDK pointed at OpenRouter's base URL. Cost is taken from the static pricing
table when the model is listed, and otherwise falls back to the actual cost
OpenRouter returns in the response usage block.
"""

from __future__ import annotations

import time
from decimal import Decimal
from typing import Iterator

from ..models import LLMChunk, LLMResponse, Message, hash_messages
from ..pricing import PricingError, cost_for
from .base import Timer, require_api_key

BASE_URL = "https://openrouter.ai/api/v1"

# Ask OpenRouter to include actual usage cost so we can fall back to it.
_USAGE_ACCOUNTING = {"include": True}


def _extra_cost(usage) -> Decimal | None:
    """Pull the provider-reported cost (USD) out of the usage object, if any."""

    cost = getattr(usage, "cost", None)
    if cost is None:
        extra = getattr(usage, "model_extra", None) or {}
        cost = extra.get("cost")
    if cost is None:
        return None
    return Decimal(str(cost))


class OpenRouterProvider:
    """Concrete provider for OpenRouter's aggregated model catalog."""

    name = "openrouter"

    def __init__(self, client=None) -> None:
        if client is None:
            import openai

            client = openai.OpenAI(
                api_key=require_api_key("OPENROUTER_API_KEY", "OpenRouter"),
                base_url=BASE_URL,
            )
        self._client = client

    def _to_payload(self, messages: list[Message]) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in messages]

    def _resolve_cost(self, model, in_tok, out_tok, usage) -> Decimal:
        """Prefer the static pricing table; fall back to OpenRouter's cost."""

        try:
            return cost_for(self.name, model, in_tok, out_tok)
        except PricingError:
            reported = _extra_cost(usage)
            if reported is not None:
                return reported
            raise PricingError(
                f"No pricing for openrouter model={model!r} and OpenRouter "
                f"returned no cost. Add it to pricing.toml."
            )

    def complete(
        self, messages: list[Message], model: str, **kwargs
    ) -> LLMResponse:
        with Timer() as timer:
            resp = self._client.chat.completions.create(
                model=model,
                messages=self._to_payload(messages),
                extra_body={"usage": _USAGE_ACCOUNTING},
                **kwargs,
            )

        choice = resp.choices[0]
        in_tok = resp.usage.prompt_tokens
        out_tok = resp.usage.completion_tokens

        return LLMResponse(
            text=choice.message.content or "",
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=self._resolve_cost(model, in_tok, out_tok, resp.usage),
            model=model,
            provider=self.name,
            latency_ms=timer.elapsed_ms,
            finish_reason=choice.finish_reason or "stop",
            prompt_hash=hash_messages(messages),
        )

    def stream(
        self, messages: list[Message], model: str, **kwargs
    ) -> Iterator[LLMChunk]:
        parts: list[str] = []
        finish_reason = "stop"
        in_tok = out_tok = 0
        usage_obj = None

        start = time.monotonic()
        stream = self._client.chat.completions.create(
            model=model,
            messages=self._to_payload(messages),
            stream=True,
            stream_options={"include_usage": True},
            extra_body={"usage": _USAGE_ACCOUNTING},
            **kwargs,
        )
        for event in stream:
            if event.choices:
                choice = event.choices[0]
                delta = choice.delta.content or ""
                if delta:
                    parts.append(delta)
                    yield LLMChunk(text=delta)
                if choice.finish_reason:
                    finish_reason = choice.finish_reason
            if event.usage:
                usage_obj = event.usage
                in_tok = event.usage.prompt_tokens
                out_tok = event.usage.completion_tokens

        latency_ms = (time.monotonic() - start) * 1000.0
        response = LLMResponse(
            text="".join(parts),
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=self._resolve_cost(model, in_tok, out_tok, usage_obj),
            model=model,
            provider=self.name,
            latency_ms=latency_ms,
            finish_reason=finish_reason,
            prompt_hash=hash_messages(messages),
        )
        yield LLMChunk(text="", finish_reason=finish_reason, response=response)
