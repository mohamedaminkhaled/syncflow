"""Provider tests. HTTP calls made by the official SDKs are mocked with respx."""

from decimal import Decimal

import anthropic
import openai
import pytest
import respx
from httpx import Response

from syncflow.llm.models import Message
from syncflow.llm.providers import ProviderError, get_provider
from syncflow.llm.providers.anthropic_provider import AnthropicProvider
from syncflow.llm.providers.openai_provider import OpenAIProvider
from syncflow.llm.providers.openrouter_provider import OpenRouterProvider

MESSAGES = [Message("user", "What is RAG?")]


def _anthropic_payload(text="Hello", in_tok=10, out_tok=20, stop="end_turn"):
    return {
        "id": "msg_1",
        "type": "message",
        "role": "assistant",
        "model": "claude-sonnet-4-5",
        "content": [{"type": "text", "text": text}],
        "stop_reason": stop,
        "stop_sequence": None,
        "usage": {"input_tokens": in_tok, "output_tokens": out_tok},
    }


def _openai_payload(text="Hi", in_tok=10, out_tok=5, finish="stop", extra_usage=None):
    usage = {"prompt_tokens": in_tok, "completion_tokens": out_tok,
             "total_tokens": in_tok + out_tok}
    if extra_usage:
        usage.update(extra_usage)
    return {
        "id": "chatcmpl-1",
        "object": "chat.completion",
        "created": 1,
        "model": "gpt-4o",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": finish,
            }
        ],
        "usage": usage,
    }


@respx.mock
def test_anthropic_complete_maps_fields():
    respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=Response(200, json=_anthropic_payload(text="RAG is...", in_tok=12, out_tok=30))
    )
    provider = AnthropicProvider(client=anthropic.Anthropic(api_key="test"))

    resp = provider.complete(MESSAGES, "claude-sonnet-4-5")

    assert resp.text == "RAG is..."
    assert resp.input_tokens == 12
    assert resp.output_tokens == 30
    assert resp.provider == "anthropic"
    assert resp.finish_reason == "end_turn"
    # 12/M*$3 + 30/M*$15 computed as Decimal
    assert resp.cost_usd == Decimal("12") / Decimal(1_000_000) * Decimal("3.00") + \
        Decimal("30") / Decimal(1_000_000) * Decimal("15.00")
    assert len(resp.prompt_hash) == 64
    assert resp.latency_ms >= 0


@respx.mock
def test_openai_complete_maps_fields():
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=Response(200, json=_openai_payload(text="Hi there", in_tok=100, out_tok=40))
    )
    provider = OpenAIProvider(client=openai.OpenAI(api_key="test"))

    resp = provider.complete(MESSAGES, "gpt-4o")

    assert resp.text == "Hi there"
    assert resp.input_tokens == 100
    assert resp.output_tokens == 40
    assert resp.provider == "openai"
    assert resp.finish_reason == "stop"
    assert resp.cost_usd == Decimal("100") / Decimal(1_000_000) * Decimal("2.50") + \
        Decimal("40") / Decimal(1_000_000) * Decimal("10.00")


@respx.mock
def test_openrouter_uses_static_pricing_table():
    # Model present in pricing.toml -> table wins, API cost ignored.
    respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
        return_value=Response(
            200,
            json=_openai_payload(
                text="ok", in_tok=1_000_000, out_tok=0,
                extra_usage={"cost": 999.0},  # bogus; must be ignored
            ),
        )
    )
    client = openai.OpenAI(api_key="test", base_url="https://openrouter.ai/api/v1")
    provider = OpenRouterProvider(client=client)

    resp = provider.complete(MESSAGES, "openai/gpt-4o")

    # 1M input tokens @ $2.50/M = $2.50 from the table, not 999.
    assert resp.cost_usd == Decimal("2.50")
    assert resp.provider == "openrouter"


@respx.mock
def test_openrouter_falls_back_to_api_cost():
    # Model NOT in pricing.toml -> use the cost OpenRouter returned.
    respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
        return_value=Response(
            200,
            json=_openai_payload(
                text="ok", in_tok=50, out_tok=10,
                extra_usage={"cost": 0.001234},
            ),
        )
    )
    client = openai.OpenAI(api_key="test", base_url="https://openrouter.ai/api/v1")
    provider = OpenRouterProvider(client=client)

    resp = provider.complete(MESSAGES, "some/unlisted-model")

    assert resp.cost_usd == Decimal("0.001234")


def test_get_provider_unknown_raises():
    with pytest.raises(ProviderError):
        get_provider("not-a-provider")


def _sse(events: list[dict]) -> bytes:
    """Encode events as an OpenAI-style text/event-stream body."""
    import json

    lines = [f"data: {json.dumps(e)}\n\n" for e in events]
    lines.append("data: [DONE]\n\n")
    return "".join(lines).encode()


def _openai_stream_events(text="Hello world", in_tok=10, out_tok=4, extra_usage=None):
    words = text.split(" ")
    events = []
    for i, w in enumerate(words):
        piece = w if i == 0 else " " + w
        events.append({
            "id": "c", "object": "chat.completion.chunk", "created": 1, "model": "gpt-4o",
            "choices": [{"index": 0, "delta": {"content": piece}, "finish_reason": None}],
        })
    events.append({
        "id": "c", "object": "chat.completion.chunk", "created": 1, "model": "gpt-4o",
        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
    })
    usage = {"prompt_tokens": in_tok, "completion_tokens": out_tok,
             "total_tokens": in_tok + out_tok}
    if extra_usage:
        usage.update(extra_usage)
    # Terminal usage-only chunk (no choices).
    events.append({
        "id": "c", "object": "chat.completion.chunk", "created": 1, "model": "gpt-4o",
        "choices": [], "usage": usage,
    })
    return events


@respx.mock
def test_openai_stream_aggregates_usage_and_cost():
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=_sse(_openai_stream_events("Hello world", in_tok=100, out_tok=40)),
        )
    )
    provider = OpenAIProvider(client=openai.OpenAI(api_key="test"))

    chunks = list(provider.stream(MESSAGES, "gpt-4o"))

    text = "".join(c.text for c in chunks)
    final = chunks[-1].response
    assert text == "Hello world"
    assert final is not None
    assert final.input_tokens == 100
    assert final.output_tokens == 40
    assert final.cost_usd == Decimal("100") / Decimal(1_000_000) * Decimal("2.50") + \
        Decimal("40") / Decimal(1_000_000) * Decimal("10.00")
    assert final.finish_reason == "stop"
    assert final.latency_ms >= 0


@respx.mock
def test_openrouter_stream_falls_back_to_api_cost():
    events = _openai_stream_events(
        "ok", in_tok=50, out_tok=10, extra_usage={"cost": 0.001234}
    )
    respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
        return_value=Response(
            200,
            headers={"content-type": "text/event-stream"},
            content=_sse(events),
        )
    )
    client = openai.OpenAI(api_key="test", base_url="https://openrouter.ai/api/v1")
    provider = OpenRouterProvider(client=client)

    chunks = list(provider.stream(MESSAGES, "some/unlisted-model"))
    final = chunks[-1].response

    assert final is not None
    assert final.cost_usd == Decimal("0.001234")
