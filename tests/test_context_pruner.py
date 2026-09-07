"""Tests for Dynamic Context Pruning and Token Optimization."""
from __future__ import annotations

import unittest
from src.utils.context_pruner import prune_and_deduplicate_sources


class TestContextPruner(unittest.TestCase):
    """Test suite validating token savings and deduplication."""

    def test_deduplication_by_url(self) -> None:
        sources = [
            {"url": "https://example.com/doc1", "snippet": "Text from doc 1", "title": "Doc 1"},
            {"url": "https://example.com/doc1", "snippet": "Duplicate URL entry", "title": "Doc 1 dup"},
            {"url": "https://example.com/doc2", "snippet": "Text from doc 2", "title": "Doc 2"},
        ]
        pruned, metrics = prune_and_deduplicate_sources(sources)
        self.assertEqual(len(pruned), 2)
        self.assertEqual(metrics["pruned_count"], 2)

    def test_length_compaction_and_savings(self) -> None:
        long_text = "Analysis of recursive reasoning. " * 100
        sources = [
            {"url": "https://example.com/long", "snippet": long_text, "title": "Long Doc"},
        ]
        pruned, metrics = prune_and_deduplicate_sources(sources, max_snippet_chars=200)
        self.assertEqual(len(pruned), 1)
        self.assertTrue(len(pruned[0]["snippet"]) <= 205)
        self.assertGreater(metrics["savings_percentage"], 0.0)


if __name__ == "__main__":
    unittest.main()
