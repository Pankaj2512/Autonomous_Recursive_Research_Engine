"""Conditional edge routing logic for the recursive research loop."""
from __future__ import annotations

import logging
from src.config import get_settings
from src.schemas.state import ResearchState

logger = logging.getLogger(__name__)


def should_recurse_or_synthesize(state: ResearchState) -> str:
    """Evaluate whether research evidence is sufficient or requires recursive iteration.

    Returns:
        "planner" if further recursive research is required.
        "synthesizer" if evidence is sufficient or recursion budget exhausted.
    """
    settings = get_settings()
    depth = state.get("recursion_depth", 0)
    max_depth = state.get("max_recursion_depth", settings.max_recursion_depth)
    history = state.get("verification_history", [])

    # Check budget
    if depth >= max_depth:
        logger.info(f"Recursion budget reached ({depth}/{max_depth}). Routing to synthesizer.")
        return "synthesizer"

    # Check verification status
    if history:
        last_eval = history[-1]
        is_sufficient = last_eval.get("sufficient", True)
        confidence = last_eval.get("confidence_score", 1.0)

        if not is_sufficient or confidence < settings.verification_threshold:
            logger.info(
                f"Information gap detected (confidence: {confidence:.2f} < {settings.verification_threshold:.2f}). "
                f"Recursing to Prime Supervisor (Depth: {depth}/{max_depth})."
            )
            return "planner"

    logger.info("Verification passed. Routing to report synthesizer.")
    return "synthesizer"
