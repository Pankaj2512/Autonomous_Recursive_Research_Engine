"""Node handlers for the LangGraph Recursive Research Engine."""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, List

from src.agents.prime_supervisor import PrimeSupervisorAgent
from src.agents.researcher import ResearchWorkerAgent
from src.agents.synthesizer import SynthesisAgent
from src.agents.verifier import VerificationAgent
from src.mcp.client import MCPClient
from src.schemas.state import ResearchState, Source, SubQuestion, VerificationAssessment
from src.utils.context_pruner import prune_and_deduplicate_sources

logger = logging.getLogger(__name__)


def planner_node(state: ResearchState) -> Dict[str, Any]:
    """Prime Supervisor planning node: decomposes goal or refines queries recursively."""
    topic = state.get("topic", "")
    depth = state.get("recursion_depth", 0)
    history = state.get("verification_history", [])
    logs = list(state.get("trace_logs", []))

    critique_reasons = []
    unresolved_gaps = []

    if history:
        last_eval = history[-1]
        if last_eval.get("reasoning"):
            critique_reasons.append(last_eval["reasoning"])
        unresolved_gaps.extend(last_eval.get("unresolved_gaps", []))

    supervisor = PrimeSupervisorAgent()
    new_sub_questions = supervisor.plan_or_refine(
        topic=topic,
        current_depth=depth,
        critique_reasons=critique_reasons,
        unresolved_gaps=unresolved_gaps,
    )

    # Convert to dicts for graph state
    existing_sq = list(state.get("sub_questions", []))
    for sq in new_sub_questions:
        existing_sq.append(sq.model_dump() if hasattr(sq, "model_dump") else sq.__dict__)

    log_entry = {
        "timestamp": time.time(),
        "node": "planner",
        "depth": depth,
        "message": f"Generated {len(new_sub_questions)} sub-questions (Recursion depth: {depth}).",
    }
    logs.append(log_entry)

    return {
        "sub_questions": existing_sq,
        "trace_logs": logs,
    }


def researcher_node(state: ResearchState) -> Dict[str, Any]:
    """Worker node: investigates pending sub-questions via Model Context Protocol (MCP)."""
    sub_questions_raw = state.get("sub_questions", [])
    existing_sources_raw = list(state.get("sources", []))
    logs = list(state.get("trace_logs", []))
    collected_evidence = list(state.get("collected_evidence", []))

    mcp_client = MCPClient()
    worker = ResearchWorkerAgent(mcp_client=mcp_client)

    updated_sub_questions = []

    for sq_dict in sub_questions_raw:
        sq = SubQuestion(**sq_dict) if isinstance(sq_dict, dict) else sq_dict
        if sq.status == "pending":
            updated_sq, new_sources = worker.research_question(sq)
            updated_sub_questions.append(
                updated_sq.model_dump() if hasattr(updated_sq, "model_dump") else updated_sq.__dict__
            )
            for src in new_sources:
                src_dict = src.model_dump() if hasattr(src, "model_dump") else src.__dict__
                existing_sources_raw.append(src_dict)

            if updated_sq.findings:
                collected_evidence.append(updated_sq.findings)
        else:
            updated_sub_questions.append(sq_dict)

    # Dynamic Context Pruning
    pruned_sources, metrics = prune_and_deduplicate_sources(existing_sources_raw)

    log_entry = {
        "timestamp": time.time(),
        "node": "researcher",
        "message": f"Investigated questions via MCP. Pruned {metrics['raw_count']} sources -> {metrics['pruned_count']}. "
                   f"Estimated token savings: {metrics['savings_percentage']}%.",
    }
    logs.append(log_entry)

    return {
        "sub_questions": updated_sub_questions,
        "sources": pruned_sources,
        "collected_evidence": collected_evidence,
        "trace_logs": logs,
    }


def verifier_node(state: ResearchState) -> Dict[str, Any]:
    """Verification and reflection node: evaluates factual grounding and detects gaps."""
    topic = state.get("topic", "")
    depth = state.get("recursion_depth", 0)
    sub_questions = [SubQuestion(**q) for q in state.get("sub_questions", [])]
    sources = [Source(**s) for s in state.get("sources", [])]
    history = list(state.get("verification_history", []))
    logs = list(state.get("trace_logs", []))

    verifier = VerificationAgent()
    assessment = verifier.evaluate(
        topic=topic,
        sub_questions=sub_questions,
        sources=sources,
        current_depth=depth,
    )

    assessment_dict = assessment.model_dump() if hasattr(assessment, "model_dump") else assessment.__dict__
    history.append(assessment_dict)

    new_depth = depth + 1

    log_entry = {
        "timestamp": time.time(),
        "node": "verifier",
        "depth": depth,
        "confidence": assessment.confidence_score,
        "hallucination_score": assessment.hallucination_score,
        "sufficient": assessment.sufficient,
        "message": f"Verification completed. Sufficient: {assessment.sufficient}, "
                   f"Confidence: {assessment.confidence_score * 100:.1f}%, Hallucination: {assessment.hallucination_score:.2f}.",
    }
    logs.append(log_entry)

    return {
        "verification_history": history,
        "recursion_depth": new_depth,
        "trace_logs": logs,
    }


def synthesizer_node(state: ResearchState) -> Dict[str, Any]:
    """Synthesis node: generates final cited markdown intelligence report."""
    topic = state.get("topic", "")
    depth = state.get("recursion_depth", 0)
    sub_questions = [SubQuestion(**q) for q in state.get("sub_questions", [])]
    sources = [Source(**s) for s in state.get("sources", [])]
    history = state.get("verification_history", [])
    logs = list(state.get("trace_logs", []))

    last_eval = VerificationAssessment(**history[-1]) if history else VerificationAssessment(
        sufficient=True, reasoning="Direct synthesis", confidence_score=0.9, hallucination_score=0.08
    )

    synthesizer = SynthesisAgent()
    final_report = synthesizer.generate_report(
        topic=topic,
        sub_questions=sub_questions,
        sources=sources,
        assessment=last_eval,
        recursion_depth=depth,
    )

    log_entry = {
        "timestamp": time.time(),
        "node": "synthesizer",
        "message": "Final cited research intelligence report compiled.",
    }
    logs.append(log_entry)

    return {
        "final_report": final_report,
        "is_complete": True,
        "trace_logs": logs,
    }
