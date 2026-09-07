"""MCP Client adapter for LangGraph agent tool dispatch."""
from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from src.mcp.server import ResearchMCPServer, get_mcp_server

logger = logging.getLogger(__name__)


class MCPClient:
    """Client adapter enabling seamless tool binding between MCP Servers and LangGraph."""

    def __init__(self, server: Optional[ResearchMCPServer] = None) -> None:
        self.server = server or get_mcp_server()

    def get_tools_for_llm(self) -> List[Dict[str, Any]]:
        """Convert MCP tool specifications into standard OpenAI/LangChain function calling definitions."""
        mcp_tools = self.server.list_tools()
        llm_tools = []
        for tool in mcp_tools:
            llm_tools.append({
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool["description"],
                    "parameters": tool["inputSchema"],
                },
            })
        return llm_tools

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Call an MCP tool and return the parsed result."""
        response = self.server.call_tool(name=tool_name, arguments=arguments)
        if response.get("isError"):
            error_msg = response.get("content", [{}])[0].get("text", "Unknown MCP error")
            logger.error(f"MCP tool call failed: {error_msg}")
            raise RuntimeError(error_msg)

        # Return structured raw result if available, or parse text
        if "raw_result" in response:
            return response["raw_result"]

        text_content = response.get("content", [{}])[0].get("text", "")
        try:
            return json.loads(text_content)
        except Exception:
            return text_content
