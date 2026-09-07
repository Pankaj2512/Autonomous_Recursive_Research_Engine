"""Prime Supervisor Agent: High-level task decomposition and recursive planning."""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List

from src.agents.llm_factory import get_chat_model
from src.config import get_settings
from src.schemas.state import SubQuestion

logger = logging.getLogger(__name__)


class PrimeSupervisorAgent:
    """The hierarchical Prime Agent supervising task decomposition and recursion budgets."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.llm = get_chat_model()

    def plan_or_refine(
        self,
        topic: str,
        current_depth: int,
        critique_reasons: List[str],
        unresolved_gaps: List[str],
    ) -> List[SubQuestion]:
        """Decompose a high-level research goal or recursively generate follow-up questions."""
        is_initial = current_depth == 0

        if is_initial:
            system_prompt = (
                "You are the Prime Supervisor of an Autonomous Recursive Research Engine. "
                "Your objective is to decompose the given research topic into 3 to 4 precise, "
                "fact-focused sub-questions that together build a comprehensive, deep intelligence report.\n"
                "Return ONLY a valid JSON array of objects with keys: 'question' and 'rationale'."
            )
            user_prompt = f"Decompose the topic: '{topic}'"
        else:
            system_prompt = (
                "You are the Prime Supervisor executing a recursive planning cycle. "
                "The previous research cycle identified specific knowledge gaps and missing evidence. "
                "Formulate 2 to 3 targeted follow-up questions specifically designed to resolve these gaps.\n"
                "Return ONLY a valid JSON array of objects with keys: 'question' and 'rationale'."
            )
            user_prompt = (
                f"Topic: '{topic}'\n"
                f"Unresolved Gaps:\n" + "\n".join(f"- {gap}" for gap in unresolved_gaps) +
                f"\nCritique Feedback:\n" + "\n".join(f"- {reason}" for reason in critique_reasons)
            )

        prompt = f"{system_prompt}\n\n{user_prompt}"

        try:
            response = self.llm.invoke(prompt)
            content = getattr(response, "content", str(response)).strip()

            # Clean JSON markdown fences
            match = re.search(r"\[.*\]", content, re.DOTALL)
            json_str = match.group(0) if match else content

            data = json.loads(json_str)
            sub_questions = []
            for item in data[:self.settings.max_sub_questions]:
                sub_questions.append(
                    SubQuestion(
                        question=item.get("question", ""),
                        rationale=item.get("rationale", ""),
                    )
                )
            return sub_questions

        except Exception as exc:
            logger.warning(f"PrimeSupervisor JSON parsing failed: {exc}. Using fallback questions.")
            if is_initial:
                return [
                    SubQuestion(question=f"What are the foundational principles and architecture of {topic}?", rationale="Core concepts"),
                    SubQuestion(question=f"What are the primary benchmarks, metrics, and empirical results for {topic}?", rationale="Empirical validation"),
                    SubQuestion(question=f"What are the key trade-offs and future developments in {topic}?", rationale="Strategic implications"),
                ]
            else:
                return [
                    SubQuestion(
                        question=f"Detailed investigation into: {gap[:80]}",
                        rationale="Targeted gap resolution",
                    )
                    for gap in unresolved_gaps[:2]
                ]
