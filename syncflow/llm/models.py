"""Normalized data models shared across all LLM providers."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Message:
    """A single chat message in a provider-agnostic form."""

    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass(frozen=True)
class LLMResponse:
    """A normalized, non-streaming completion result.

    Every provider translates its native response into this shape so the
    rest of the application never depends on a specific SDK.
    """

    text: str
    input_tokens: int
    output_tokens: int
    cost_usd: Decimal
    model: str
    provider: str
    latency_ms: float
    finish_reason: str
    prompt_hash: str  # sha256 of the request messages (for caching / replay)


@dataclass(frozen=True)
class LLMChunk:
    """A single streamed delta from a provider.

    The terminal chunk (the one carrying ``finish_reason``) also populates
    ``response`` with the fully-aggregated :class:`LLMResponse` — including
    token counts, cost and latency — once the stream completes.
    """

    text: str
    finish_reason: str | None = None
    response: LLMResponse | None = None


def hash_messages(messages: list[Message]) -> str:
    """Return a stable sha256 hex digest for a list of messages.

    The digest is computed over a canonical JSON representation so identical
    conversations always hash to the same value regardless of object identity.
    """

    canonical = json.dumps(
        [{"role": m.role, "content": m.content} for m in messages],
        separators=(",", ":"),
        ensure_ascii=False,
        sort_keys=True,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
