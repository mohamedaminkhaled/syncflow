"""Provider registry / factory."""

from __future__ import annotations

from .anthropic_provider import AnthropicProvider
from .base import LLMProvider, ProviderError
from .openai_provider import OpenAIProvider
from .openrouter_provider import OpenRouterProvider

_REGISTRY: dict[str, type] = {
    AnthropicProvider.name: AnthropicProvider,
    OpenAIProvider.name: OpenAIProvider,
    OpenRouterProvider.name: OpenRouterProvider,
}

PROVIDERS = tuple(_REGISTRY)


def get_provider(name: str, **kwargs) -> LLMProvider:
    """Instantiate a provider by name.

    Raises :class:`ProviderError` for unknown providers.
    """

    try:
        cls = _REGISTRY[name]
    except KeyError:
        known = ", ".join(sorted(_REGISTRY))
        raise ProviderError(
            f"Unknown provider {name!r}. Available providers: {known}."
        ) from None
    return cls(**kwargs)


__all__ = [
    "LLMProvider",
    "ProviderError",
    "AnthropicProvider",
    "OpenAIProvider",
    "OpenRouterProvider",
    "get_provider",
    "PROVIDERS",
]
