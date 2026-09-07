"""Synthesis Agent: Produces comprehensive, cited markdown intelligence reports."""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from src.agents.llm_factory import get_chat_model
from src.schemas.state import Source, SubQuestion, VerificationAssessment

logger = logging.getLogger(__name__)


class SynthesisAgent:
    """Compiles verified findings and evidence into a structured markdown report."""

    def __init__(self) -> None:
        self.llm = get_chat_model()

    def generate_report(
        self,
        topic: str,
        sub_questions: List[SubQuestion],
        sources: List[Source],
        assessment: VerificationAssessment,
        recursion_depth: int,
    ) -> str:
        """Synthesize all research findings into a final document."""
        # Prepare context blocks
        q_and_a = []
        for i, q in enumerate(sub_questions, 1):
            q_and_a.append(f"### Sub-Question {i}: {q.question}\n**Rationale:** {q.rationale}\n**Verified Findings:**\n{q.findings or 'N/A'}\n")

        q_and_a_text = "\n".join(q_and_a)

        citations_list = []
        for s in sources:
            citations_list.append(f"- [{s.id}] [{s.title}]({s.url}) (Relevance: {s.relevance_score:.2f})")
        citations_text = "\n".join(citations_list) if citations_list else "No external web sources retrieved."

        prompt = (
            "You are a Principal Intelligence Synthesizer. Generate an exhaustive, publication-grade "
            "research briefing based solely on the verified findings below.\n\n"
            f"# Topic: {topic}\n"
            f"Research Iterations Completed: {recursion_depth}\n"
            f"Verification Confidence: {assessment.confidence_score * 100:.1f}%\n"
            f"Grounding / Hallucination Score: {assessment.hallucination_score:.2f}\n\n"
            f"## Verified Research Evidence:\n{q_and_a_text}\n\n"
            f"## Citations Catalog:\n{citations_text}\n\n"
            "Formatting Guidelines:\n"
            "1. Output a beautifully structured GitHub-flavored Markdown report.\n"
            "2. Include: Title, Executive Summary, Key Insights & Architectural Takeaways, "
            "Detailed Analysis, Verification Audit section, and References.\n"
            "3. Reference inline source tags [id] accurately.\n"
            "4. Do NOT hallucinate information not supported by the evidence."
        )

        try:
            response = self.llm.invoke(prompt)
            report = getattr(response, "content", str(response)).strip()
            return report
        except Exception as exc:
            logger.error(f"Synthesis generation failed: {exc}")
            # Fallback report compilation
            return (
                f"# Autonomous Research Report: {topic}\n\n"
                f"**Verification Confidence:** {assessment.confidence_score * 100:.1f}% | "
                f"**Recursion Cycles:** {recursion_depth}\n\n"
                f"## Executive Summary\n"
                f"This report presents synthesized intelligence on **{topic}** gathered via "
                f"recursive multi-agent decomposition and verified against live sources.\n\n"
                f"## Research Inquiries & Findings\n\n{q_and_a_text}\n\n"
                f"## Verification Audit\n"
                f"- **Audit Status:** {'PASSED' if assessment.sufficient else 'PROVISIONAL'}\n"
                f"- **Critique Note:** {assessment.reasoning}\n\n"
                f"## References\n\n{citations_text}\n"
            )
