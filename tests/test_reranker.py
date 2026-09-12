"""Tests for Hybrid Re-Ranking and Report Exporter."""
from __future__ import annotations

import unittest
from src.utils.exporter import generate_html_report
from src.utils.reranker import hybrid_rerank_passages


class TestHybridReranker(unittest.TestCase):
    """Test suite validating BM25 + semantic vector fusion re-ranking."""

    def test_hybrid_reranking_order(self) -> None:
        query = "recursive language model multi agent"
        passages = [
            {
                "text": "Weather forecast in London is cloudy with rain.",
                "title": "Weather",
                "score": 0.1,
            },
            {
                "text": "Recursive language model architectures coordinate multi-agent inquiry trees.",
                "title": "RLM Paper",
                "score": 0.85,
            },
            {
                "text": "A general language model can perform text generation tasks.",
                "title": "General LLM",
                "score": 0.6,
            },
        ]

        reranked = hybrid_rerank_passages(query=query, passages=passages, alpha=0.6, top_k=2)
        self.assertEqual(len(reranked), 2)
        self.assertEqual(reranked[0]["title"], "RLM Paper")
        self.assertGreater(reranked[0]["hybrid_score"], reranked[1]["hybrid_score"])
        self.assertIn("lexical_score", reranked[0])
        self.assertIn("semantic_score", reranked[0])

    def test_empty_passages_handling(self) -> None:
        result = hybrid_rerank_passages("query", [])
        self.assertEqual(result, [])


class TestReportExporter(unittest.TestCase):
    """Test suite validating HTML report rendering."""

    def test_generate_html_report(self) -> None:
        md = "# Sample Title\n\n## Summary\nThis is a test report.\n\n- Key Point 1\n- Key Point 2\n"
        html_out = generate_html_report(md, "Test Topic", {"confidence": 94.0, "hallucination_score": 0.05})

        self.assertIn("<!DOCTYPE html>", html_out)
        self.assertIn("Test Topic", html_out)
        self.assertIn("94.0%", html_out)
        self.assertIn("Sample Title", html_out)
        self.assertIn("<li>Key Point 1</li>", html_out)


if __name__ == "__main__":
    unittest.main()
