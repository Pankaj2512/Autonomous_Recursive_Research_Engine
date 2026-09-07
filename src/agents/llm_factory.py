"""Multi-provider LLM initialization factory with graceful fallback."""
from __future__ import annotations

import logging
from typing import Any, List, Optional

from src.config import get_settings

logger = logging.getLogger(__name__)


class MockAIMessage:
    """Mock LLM response for local testing and zero-API-key demonstration."""
    def __init__(self, content: str) -> None:
        self.content = content


class MockChatModel:
    """Deterministic fallback mock model simulating LLM behavior for dry runs."""
    def __init__(self, model_name: str = "mock-agent-engine") -> None:
        self.model_name = model_name

    def invoke(self, messages: Any) -> MockAIMessage:
        # Extract prompt content
        prompt_text = ""
        if isinstance(messages, list) and messages:
            last = messages[-1]
            prompt_text = getattr(last, "content", str(last))
        elif isinstance(messages, str):
            prompt_text = messages

        # Heuristic simulation based on agent prompts
        if "Audit and Verification" in prompt_text or "fact-check" in prompt_text or "critique" in prompt_text:
            content = (
                '{\n'
                '  "sufficient": true,\n'
                '  "hallucination_score": 0.08,\n'
                '  "confidence_score": 0.92,\n'
                '  "reasoning": "Collected source findings provide grounded facts with concrete citations.",\n'
                '  "unresolved_gaps": [],\n'
                '  "suggested_followups": []\n'
                '}'
            )
        elif "Decompose the topic" in prompt_text or "Prime Agent" in prompt_text or "Prime Supervisor" in prompt_text:
            content = (
                '[\n'
                '  {"question": "What are the core technical mechanisms and architectural bottlenecks?", "rationale": "Understand technical principles and constraints."},\n'
                '  {"question": "What empirical benchmarks and performance metrics exist?", "rationale": "Quantify real-world effectiveness."},\n'
                '  {"question": "What are the leading industrial trade-offs and future developments?", "rationale": "Provide forward-looking strategic context."}\n'
                ']'
            )
        elif "Synthesizer" in prompt_text or "Final Report" in prompt_text:
            content = (
                "# Executive Research Brief\n\n"
                "## Key Findings\n"
                "- Demonstrated empirical efficiency gains and verified scalability.\n"
                "- Successfully grounded claims across indexed source material.\n\n"
                "## Detailed Technical Analysis\n"
                "The system integrates recursive language model decomposition with real-time tool grounding, "
                "reducing token consumption and eliminating ungrounded speculation.\n\n"
                "## Citations\n"
                "1. Multi-Agent Recursive Framework Whitepaper (2025)\n"
                "2. Model Context Protocol Specifications\n"
            )
        else:
            content = f"Synthesized findings based on evidence: {prompt_text[:120]}..."

        return MockAIMessage(content=content)


def get_chat_model(override_provider: Optional[str] = None, override_model: Optional[str] = None) -> Any:
    """Instantiate configured LLM provider or fallback to mock runner.

    Supported providers: 'openai', 'gemini', 'groq', 'ollama', 'mock'.
    """
    settings = get_settings()
    provider = (override_provider or settings.llm_provider).lower()
    model_name = override_model or settings.llm_model
    temp = settings.llm_temperature

    try:
        if provider == "openai":
            if not settings.openai_api_key:
                logger.warning("OPENAI_API_KEY not found; falling back to MockChatModel.")
                return MockChatModel(model_name=model_name)
            from langchain_openai import ChatOpenAI
            return ChatOpenAI(model=model_name, temperature=temp, api_key=settings.openai_api_key)

        elif provider in ("gemini", "google"):
            if not settings.gemini_api_key:
                logger.warning("GEMINI_API_KEY not found; falling back to MockChatModel.")
                return MockChatModel(model_name=model_name)
            from langchain_google_genai import ChatGoogleGenerativeAI
            return ChatGoogleGenerativeAI(model=model_name, temperature=temp, google_api_key=settings.gemini_api_key)

        elif provider == "groq":
            if not settings.groq_api_key:
                logger.warning("GROQ_API_KEY not found; falling back to MockChatModel.")
                return MockChatModel(model_name=model_name)
            from langchain_groq import ChatGroq
            return ChatGroq(model_name=model_name, temperature=temp, groq_api_key=settings.groq_api_key)

        elif provider == "ollama":
            from langchain_community.chat_models import ChatOllama
            return ChatOllama(model=model_name, base_url=settings.ollama_base_url, temperature=temp)

        else:
            return MockChatModel(model_name=model_name)

    except Exception as exc:
        logger.warning(f"Failed to load provider '{provider}': {exc}. Using simulated MockChatModel.")
        return MockChatModel(model_name=model_name)
