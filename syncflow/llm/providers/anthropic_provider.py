"""Anthropic provider built on the official ``anthropic`` SDK."""

from __future__ import annotations

import time
from typing import Iterator

from ..models import LLMChunk, LLMResponse, Message, hash_messages
from ..pricing import cost_for
from .base import Timer, require_api_key

DEFAULT_MAX_TOKENS = 1024


def _split_system(messages: list[Message]) -> tuple[str | None, list[dict]]:
    """Anthropic takes the system prompt separately from the message list."""

    system: str | None = None
    chat: list[dict] = []
    for m in messages:
        if m.role == "system":
            system = m.content if system is None else f"{system}\n{m.content}"
        else:
            chat.append({"role": m.role, "content": m.content})
    return system, chat


class AnthropicProvider:
    """Concrete :class:`~syncflow.llm.providers.base.LLMProvider`."""

    name = "anthropic"

    def __init__(self, client=None) -> None:
        # Imported lazily so the package imports without the SDK installed.
        if client is None:
            import anthropic

            client = anthropic.Anthropic(
                api_key=require_api_key("ANTHROPIC_API_KEY", "Anthropic")
            )
        self._client = client

    def complete(
        self, messages: list[Message], model: str, **kwargs
    ) -> LLMResponse:
        system, chat = _split_system(messages)
        max_tokens = kwargs.pop("max_tokens", DEFAULT_MAX_TOKENS)

        with Timer() as timer:
            resp = self._client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system or "",
                messages=chat,
                **kwargs,
            )

        text = "".join(
            block.text for block in resp.content if getattr(block, "type", "") == "text"
        )
        in_tok = resp.usage.input_tokens
        out_tok = resp.usage.output_tokens

        return LLMResponse(
            text=text,
            input_tokens=in_tok,
            output_tokens=out_tok,
            cost_usd=cost_for(self.name, model, in_tok, out_tok),
            model=model,
            provider=self.name,
            latency_ms=timer.elapsed_ms,
            finish_reason=resp.stop_reason or "stop",
            prompt_hash=hash_messages(messages),
        )

    def stream(
        self, messages: list[Message], model: str, **kwargs
    ) -> Iterator[LLMChunk]:
        system, chat = _split_system(messages)
        max_tokens = kwargs.pop("max_tokens", DEFAULT_MAX_TOKENS)

        parts: list[str] = []
        start = time.monotonic()
        with self._client.messages.stream(
            model=model,
            max_tokens=max_tokens,
            system=system or "",
            messages=chat,
            **kwargs,
        ) as stream:
            for text in stream.text_stream:
                parts.append(text)
                yield LLMChunk(text=text)
            final = stream.get_final_message()

        latency_ms = (time.monotonic() - start) * 1000.0
        in_tok = final.usage.input_tokens
        out_tok = final.usage.output_tokens
        finish_reason = final.stop_reason or "stop"
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
