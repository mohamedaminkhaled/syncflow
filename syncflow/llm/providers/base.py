"""Provider abstraction: the Protocol every LLM provider must satisfy."""

from __future__ import annotations

import os
import time
from typing import Iterator, Protocol, runtime_checkable

from ..models import LLMChunk, LLMResponse, Message


@runtime_checkable
class LLMProvider(Protocol):
    """Structural interface implemented by every concrete provider."""

    name: str

    def complete(
        self, messages: list[Message], model: str, **kwargs
    ) -> LLMResponse: ...

    def stream(
        self, messages: list[Message], model: str, **kwargs
    ) -> Iterator[LLMChunk]: ...


class ProviderError(RuntimeError):
    """Raised for configuration or provider-side problems."""


def require_api_key(env_var: str, provider_name: str) -> str:
    """Fetch an API key from the environment or raise a helpful error."""

    key = os.environ.get(env_var)
    if not key:
        raise ProviderError(
            f"Missing API key for {provider_name}. "
            f"Set the {env_var} environment variable."
        )
    return key


class Timer:
    """Monotonic-clock timer.

    Uses ``time.monotonic()`` so elapsed time can never go backwards if the
    system wall clock is adjusted mid-request.
    """

    def __init__(self) -> None:
        self._start = 0.0
        self.elapsed_ms = 0.0

    def __enter__(self) -> "Timer":
        self._start = time.monotonic()
        return self

    def __exit__(self, *exc) -> None:
        self.elapsed_ms = (time.monotonic() - self._start) * 1000.0
