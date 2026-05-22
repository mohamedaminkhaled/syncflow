"""Pricing table loader and cost calculation.

Costs are computed with :class:`decimal.Decimal` end-to-end. Floating point
must never touch money math.
"""

from __future__ import annotations

import tomllib
from decimal import Decimal
from functools import lru_cache
from pathlib import Path

_PRICING_PATH = Path(__file__).with_name("pricing.toml")
_PER_MILLION = Decimal(1_000_000)


class PricingError(LookupError):
    """Raised when a (provider, model) pair has no known pricing."""


@lru_cache(maxsize=1)
def load_pricing(path: str | None = None) -> dict[str, dict[str, dict[str, Decimal]]]:
    """Load and cache the pricing table.

    Returns a nested mapping: ``provider -> model -> {"input"/"output": Decimal}``.
    """

    target = Path(path) if path else _PRICING_PATH
    with target.open("rb") as fh:
        raw = tomllib.load(fh)

    table: dict[str, dict[str, dict[str, Decimal]]] = {}
    for provider, models in raw.items():
        table[provider] = {}
        for model, rates in models.items():
            table[provider][model] = {
                "input": Decimal(str(rates["input_per_million_usd"])),
                "output": Decimal(str(rates["output_per_million_usd"])),
            }
    return table


def get_rates(provider: str, model: str) -> dict[str, Decimal] | None:
    """Return the per-million input/output rates, or ``None`` if unknown."""

    return load_pricing().get(provider, {}).get(model)


def list_models() -> dict[str, list[str]]:
    """Return ``{provider: [model, ...]}`` from the pricing table.

    Used to populate UI dropdowns so the catalog stays in sync with pricing.
    """

    return {provider: list(models) for provider, models in load_pricing().items()}


def cost_for(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
) -> Decimal:
    """Compute the USD cost for a request from the static pricing table.

    Raises :class:`PricingError` when the model is not present in the table.
    Callers that have a provider-supplied cost (e.g. OpenRouter) should catch
    this and fall back to that value.
    """

    rates = get_rates(provider, model)
    if rates is None:
        raise PricingError(f"No pricing for provider={provider!r} model={model!r}")

    input_cost = (Decimal(input_tokens) / _PER_MILLION) * rates["input"]
    output_cost = (Decimal(output_tokens) / _PER_MILLION) * rates["output"]
    return input_cost + output_cost
