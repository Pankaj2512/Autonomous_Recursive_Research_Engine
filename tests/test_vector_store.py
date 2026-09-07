"""Tests for Vector Store and Semantic Search."""
from __future__ import annotations

import unittest
from src.tools.vector_store import VectorMemoryStore, get_vector_store


class TestVectorMemoryStore(unittest.TestCase):
    """Test suite for semantic vector indexing and similarity retrieval."""

    def setUp(self) -> None:
        self.store = VectorMemoryStore(collection_name="test_collection")
        self.store.clear()

    def test_add_and_count_documents(self) -> None:
        doc_id = self.store.add_document(
            text="LangGraph enables stateful, multi-agent coordination with recursive cycles.",
            title="LangGraph Overview",
            url="https://example.com/langgraph",
        )
        self.assertTrue(len(doc_id) > 0)
        self.assertEqual(self.store.count(), 1)

    def test_semantic_search_ranking(self) -> None:
        self.store.add_document(
            text="Quantum computing utilizes qubits to perform superposition and entanglement calculations.",
            title="Quantum Basics",
            url="https://example.com/quantum",
        )
        self.store.add_document(
            text="Recursive Language Models decompose complex queries into hierarchical DAG execution trees.",
            title="RLM Architecture",
            url="https://example.com/rlm",
        )

        hits = self.store.search(query="recursive execution trees in agents", top_k=1)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0]["title"], "RLM Architecture")
        self.assertGreater(hits[0]["score"], 0.0)

    def test_empty_query_handling(self) -> None:
        hits = self.store.search(query="", top_k=5)
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
