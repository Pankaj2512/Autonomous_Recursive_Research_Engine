"""StateGraph compilation and execution workflow for Autonomous Recursive Research Engine."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from src.config import get_settings
from src.graph.edges import should_recurse_or_synthesize
from src.graph.nodes import (
    planner_node,
    researcher_node,
    synthesizer_node,
    verifier_node,
)
from src.schemas.state import ResearchState

logger = logging.getLogger(__name__)


def create_research_graph() -> Any:
    """Construct and compile the recursive LangGraph workflow."""
    try:
        from langgraph.graph import END, START, StateGraph

        workflow = StateGraph(ResearchState)

        # Register execution nodes
        workflow.add_node("planner", planner_node)
        workflow.add_node("researcher", researcher_node)
        workflow.add_node("verifier", verifier_node)
        workflow.add_node("synthesizer", synthesizer_node)

        # Static edges
        workflow.add_edge(START, "planner")
        workflow.add_edge("planner", "researcher")
        workflow.add_edge("researcher", "verifier")

        # Recursive conditional edge
        workflow.add_conditional_edges(
            "verifier",
            should_recurse_or_synthesize,
            {
                "planner": "planner",
                "synthesizer": "synthesizer",
            },
        )

        workflow.add_edge("synthesizer", END)

        return workflow.compile()

    except ImportError:
        logger.warning("LangGraph not installed in active environment. Using pure-Python compiled graph runner.")
        return FallbackGraphRunner()


class FallbackGraphRunner:
    """Pure-Python execution engine executing the identical DAG state transitions."""

    def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute state through planner -> researcher -> verifier -> (recursive loop) -> synthesizer."""
        current_state = dict(state)
        settings = get_settings()
        max_depth = current_state.get("max_recursion_depth", settings.max_recursion_depth)

        while True:
            # 1. Planner Node
            update = planner_node(current_state)  # type: ignore[arg-type]
            current_state.update(update)

            # 2. Researcher Node (dispatches MCP tools)
            update = researcher_node(current_state)  # type: ignore[arg-type]
            current_state.update(update)

            # 3. Verifier Node (reflection & audit)
            update = verifier_node(current_state)  # type: ignore[arg-type]
            current_state.update(update)

            # 4. Conditional Edge Evaluation
            route = should_recurse_or_synthesize(current_state)  # type: ignore[arg-type]
            if route == "planner" and current_state.get("recursion_depth", 0) < max_depth:
                continue
            else:
                break

        # 5. Synthesizer Node
        final_update = synthesizer_node(current_state)  # type: ignore[arg-type]
        current_state.update(final_update)

        return current_state


def run_research_workflow(
    topic: str,
    max_depth: Optional[int] = None,
) -> Dict[str, Any]:
    """High-level runner initiating an end-to-end research session.

    Args:
        topic: The user's target research inquiry.
        max_depth: Optional override for maximum recursion cycles.

    Returns:
        Final research state including the verified report and execution logs.
    """
    settings = get_settings()
    depth_limit = max_depth if max_depth is not None else settings.max_recursion_depth

    initial_state: ResearchState = {
        "topic": topic,
        "recursion_depth": 0,
        "max_recursion_depth": depth_limit,
        "sub_questions": [],
        "sources": [],
        "collected_evidence": [],
        "verification_history": [],
        "is_complete": False,
        "final_report": None,
        "trace_logs": [],
        "error_log": [],
    }

    graph = create_research_graph()
    final_state = graph.invoke(initial_state)
    return final_state
