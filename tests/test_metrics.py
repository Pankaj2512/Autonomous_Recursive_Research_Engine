"""Tests for Token Cost Estimation and Node Latency Metrics."""
from __future__ import annotations

import unittest
from src.config import estimate_token_cost, MODEL_PRICING_PER_1M


class TestTokenMetrics(unittest.TestCase):
    """Test suite validating token pricing calculation and model rate lookups."""

    def test_gpt4o_mini_cost_calculation(self) -> None:
        # 1M prompt ($0.15) + 1M completion ($0.60) = $0.75
        cost = estimate_token_cost(prompt_tokens=1_000_000, completion_tokens=1_000_000, model_name="gpt-4o-mini")
        self.assertAlmostEqual(cost, 0.75, places=4)

    def test_default_pricing_fallback(self) -> None:
        cost = estimate_token_cost(prompt_tokens=100_000, completion_tokens=50_000, model_name="unknown-custom-model")
        self.assertGreater(cost, 0.0)

    def test_zero_tokens_returns_zero(self) -> None:
        cost = estimate_token_cost(prompt_tokens=0, completion_tokens=0)
        self.assertEqual(cost, 0.0)


if __name__ == "__main__":
    unittest.main()
