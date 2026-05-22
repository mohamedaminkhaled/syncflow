"""OpenAI provider built on the official ``openai`` SDK."""

from __future__ import annotations

import time
from typing import Iterator

from ..models import LLMChunk, LLMResponse, Message, hash_messages
from ..pricing import cost_for
from .base import Timer, require_api_key


class OpenAIProvider:
    """Concrete provider using the OpenAI Chat Completions API."""

    name = "openai"

    def __init__(self, client=None) -> None:
        if client is None:
            import openai

            client = openai.OpenAI(
                api_key=require_api_key("OPENAI_API_KEY", "OpenAI")
            )
        self._client = client

    def _to_payload(self, messages: list[Message]) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in messages]

    def complete(
        self, messages: list[Message], model: str, **kwargs
    ) -> LLMResponse:
        with Timer() as timer:
            resp = self._client.chat.completions.create(
                model=model,
                messages=self._to_payload(messages),
                **kwargs,
            )

        choice = resp.choices[0]
        in_tok = resp.usage.prompt_tokens
        out_tok = resp.usage.completion_tokens

        return LLMResponse(
            text=choice.message.content or "",
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=cost_for(self.name, model, in_tok, out_tok),
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

        start = time.monotonic()
        stream = self._client.chat.completions.create(
            model=model,
            messages=self._to_payload(messages),
            stream=True,
            stream_options={"include_usage": True},
            **kwargs,
        )
        for event in stream:
            # The usage-only terminal event carries no choices.
            if event.choices:
                choice = event.choices[0]
                delta = choice.delta.content or ""
                if delta:
                    parts.append(delta)
                    yield LLMChunk(text=delta)
                if choice.finish_reason:
                    finish_reason = choice.finish_reason
            if event.usage:
                in_tok = event.usage.prompt_tokens
                out_tok = event.usage.completion_tokens

        latency_ms = (time.monotonic() - start) * 1000.0
        response = LLMResponse(
            text="".join(parts),
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=cost_for(self.name, model, in_tok, out_tok),
            model=model,
            provider=self.name,
            latency_ms=latency_ms,
            finish_reason=finish_reason,
            prompt_hash=hash_messages(messages),
        )
        yield LLMChunk(text="", finish_reason=finish_reason, response=response)
