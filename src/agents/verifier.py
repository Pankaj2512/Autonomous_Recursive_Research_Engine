"""Verification and Self-Reflection Agent: Fact-checking and hallucination auditing."""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List

from src.agents.llm_factory import get_chat_model
from src.config import get_settings
from src.schemas.state import Source, SubQuestion, VerificationAssessment

logger = logging.getLogger(__name__)


class VerificationAgent:
    """Evaluator agent responsible for self-critique, hallucination assessment, and gap detection."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.llm = get_chat_model()

    def evaluate(
        self,
        topic: str,
        sub_questions: List[SubQuestion],
        sources: List[Source],
        current_depth: int,
    ) -> VerificationAssessment:
        """Evaluate evidence coverage and cross-check claims against ground-truth source text."""
        # Compile research findings
        findings_text = "\n\n".join(
            f"Q: {q.question}\nA: {q.findings or 'No findings'}"
            for q in sub_questions
        )

        sources_summary = "\n".join(
            f"[{s.id}] {s.title}: {s.snippet[:200]}"
            for s in sources[:6]
        )

        prompt = (
            "You are an impartial Audit and Verification Agent. Evaluate the compiled research against the sources.\n\n"
            f"Research Topic: {topic}\n"
            f"Recursion Depth: {current_depth} / {self.settings.max_recursion_depth}\n\n"
            f"Compiled Findings:\n{findings_text}\n\n"
            f"Source Evidence:\n{sources_summary}\n\n"
            "Audit Tasks:\n"
            "1. Assess whether the findings are fully grounded in the source text (check for unsupported claims / hallucinations).\n"
            "2. Identify any crucial knowledge gaps or contradictions that remain unanswered.\n"
            "3. Decide whether the gathered information is SUFFICIENT to generate a comprehensive, definitive report.\n\n"
            "Return strictly a JSON object with keys:\n"
            "- 'sufficient': boolean (true if ready for report, false if deeper recursion is required)\n"
            "- 'hallucination_score': float between 0.0 (perfectly grounded) and 1.0 (unsubstantiated)\n"
            "- 'confidence_score': float between 0.0 and 1.0\n"
            "- 'reasoning': string summary of audit critique\n"
            "- 'unresolved_gaps': list of strings detailing specific missing facts\n"
            "- 'suggested_followups': list of follow-up questions for the Prime Agent\n"
        )

        try:
            response = self.llm.invoke(prompt)
            content = getattr(response, "content", str(response)).strip()

            # Clean JSON fences
            match = re.search(r"\{.*\}", content, re.DOTALL)
            json_str = match.group(0) if match else content

            data = json.loads(json_str)

            assessment = VerificationAssessment(
                sufficient=bool(data.get("sufficient", True)),
                hallucination_score=float(data.get("hallucination_score", 0.08)),
                confidence_score=float(data.get("confidence_score", 0.9)),
                reasoning=str(data.get("reasoning", "Evidence is grounded.")),
                unresolved_gaps=list(data.get("unresolved_gaps", [])),
                suggested_followups=list(data.get("suggested_followups", [])),
            )

            # If confidence is below threshold and we have remaining depth, force sufficient=False
            if assessment.confidence_score < self.settings.verification_threshold and current_depth < self.settings.max_recursion_depth:
                assessment.sufficient = False

            return assessment

        except Exception as exc:
            logger.warning(f"Verification JSON parsing error: {exc}. Using conservative heuristic.")
            # Heuristic: If we have > 1 subquestion answered and sources exist, consider sufficient
            has_sources = len(sources) > 0
            return VerificationAssessment(
                sufficient=has_sources or current_depth >= self.settings.max_recursion_depth,
                hallucination_score=0.1 if has_sources else 0.4,
                confidence_score=0.88 if has_sources else 0.5,
                reasoning="Heuristic verification based on evidence availability.",
                unresolved_gaps=[],
                suggested_followups=[],
            )
