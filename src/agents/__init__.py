"""Agents implementing the Recursive Language Model (RLM) pattern."""
from __future__ import annotations

from src.agents.llm_factory import get_chat_model
from src.agents.prime_supervisor import PrimeSupervisorAgent
from src.agents.researcher import ResearchWorkerAgent
from src.agents.synthesizer import SynthesisAgent
from src.agents.verifier import VerificationAgent

__all__ = [
    "PrimeSupervisorAgent",
    "ResearchWorkerAgent",
    "SynthesisAgent",
    "VerificationAgent",
    "get_chat_model",
]
