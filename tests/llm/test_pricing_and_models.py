"""Pure-Python tests for pricing math and message hashing (no network)."""

from decimal import Decimal

import pytest

from syncflow.llm.models import Message, hash_messages
from syncflow.llm.pricing import PricingError, cost_for


def test_cost_for_decimal_precision():
    # 1,000,000 input tokens @ $3/M + 500,000 output tokens @ $15/M
    # = 3.00 + 7.50 = 10.50, exactly, with no float drift.
    cost = cost_for("anthropic", "claude-sonnet-4-5", 1_000_000, 500_000)
    assert isinstance(cost, Decimal)
    assert cost == Decimal("10.50")


def test_cost_for_unknown_model_raises():
    with pytest.raises(PricingError):
        cost_for("anthropic", "does-not-exist", 100, 100)


def test_hash_messages_is_stable_and_content_sensitive():
    a = [Message("user", "What is RAG?")]
    b = [Message("user", "What is RAG?")]
    c = [Message("user", "What is HNSW?")]

    assert hash_messages(a) == hash_messages(b)
    assert hash_messages(a) != hash_messages(c)
    # sha256 hex digest length
    assert len(hash_messages(a)) == 64
