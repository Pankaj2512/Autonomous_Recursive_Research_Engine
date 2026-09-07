"""Worker Agent: Dispatches MCP search and scraper tools to gather evidence."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

from src.agents.llm_factory import get_chat_model
from src.mcp.client import MCPClient
from src.schemas.state import Source, SubQuestion

logger = logging.getLogger(__name__)


class ResearchWorkerAgent:
    """Worker agent executing targeted investigations via Model Context Protocol (MCP)."""

    def __init__(self, mcp_client: MCPClient) -> None:
        self.mcp = mcp_client
        self.llm = get_chat_model()

    def research_question(self, sub_q: SubQuestion) -> Tuple[SubQuestion, List[Source]]:
        """Investigate a single sub-question via MCP tools and summarize findings."""
        # 1. Dispatch web search via MCP tool standard
        try:
            search_results = self.mcp.execute_tool(
                "web_search",
                {"query": sub_q.question, "max_results": 3},
            )
        except Exception as exc:
            logger.warning(f"MCP search call failed for '{sub_q.question}': {exc}")
            search_results = []

        sources: List[Source] = []
        snippets_text = []

        for item in search_results:
            src = Source(
                url=item.get("url", ""),
                title=item.get("title", "Web Source"),
                snippet=item.get("snippet", ""),
                relevance_score=float(item.get("score", 0.8)),
            )
            sources.append(src)
            snippets_text.append(f"[{src.id}] {src.title}: {src.snippet}")

        context_block = "\n".join(snippets_text) if snippets_text else "No external search snippets returned."

        # 2. Synthesize intermediate findings using LLM
        prompt = (
            "You are a Senior Research Worker Agent. Analyze the retrieved context to answer the sub-question.\n"
            f"Sub-question: {sub_q.question}\n"
            f"Rationale: {sub_q.rationale}\n\n"
            f"Retrieved Evidence:\n{context_block}\n\n"
            "Provide a concise, factual summary answering the question. "
            "Cite source IDs in brackets (e.g. [id]) where applicable. "
            "If evidence is weak, state the uncertainty explicitly."
        )

        try:
            response = self.llm.invoke(prompt)
            findings = getattr(response, "content", str(response)).strip()
        except Exception as exc:
            logger.error(f"Worker LLM synthesis failed: {exc}")
            findings = f"Preliminary evidence gathered for {sub_q.question}. Context: {context_block[:300]}"

        # Update sub-question state
        sub_q.findings = findings
        sub_q.status = "researched"
        sub_q.confidence_score = 0.85 if snippets_text else 0.4
        sub_q.source_ids = [s.id for s in sources]

        return sub_q, sources
