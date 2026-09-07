"""Integration tests for Recursive Research Workflow."""
from __future__ import annotations

import unittest
from src.graph.workflow import run_research_workflow


class TestResearchWorkflow(unittest.TestCase):
    """End-to-end integration test validating state transitions."""

    def test_run_workflow_execution(self) -> None:
        topic = "Model Context Protocol Integration"
        final_state = run_research_workflow(topic=topic, max_depth=1)

        self.assertTrue(final_state.get("is_complete"))
        self.assertIsNotNone(final_state.get("final_report"))
        self.assertGreater(len(final_state.get("sub_questions", [])), 0)
        self.assertGreater(len(final_state.get("trace_logs", [])), 0)

        # Validate verifier assessment exists
        history = final_state.get("verification_history", [])
        self.assertGreater(len(history), 0)
        self.assertIn("confidence_score", history[0])


if __name__ == "__main__":
    unittest.main()
