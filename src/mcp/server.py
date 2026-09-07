"""Custom Model Context Protocol (MCP) Server for Research Tools."""
from __future__ import annotations

import json
import logging
import sys
from typing import Any, Callable, Dict, List, Optional

from src.tools.scraper import scrape_url_content
from src.tools.search import perform_web_search
from src.tools.vector_store import index_document, search_vector_store

logger = logging.getLogger(__name__)


class ResearchMCPServer:
    """Standard Model Context Protocol (MCP) Server implementation for research agents."""

    def __init__(self, server_name: str = "research-mcp-server", version: str = "1.0.0") -> None:
        self.server_name = server_name
        self.version = version
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._handlers: Dict[str, Callable[..., Any]] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        """Register the built-in MCP search and scraping tools."""
        self.register_tool(
            name="web_search",
            description="Searches the live web for targeted research queries and returns ranked snippets.",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Specific, factual search query to investigate.",
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of search results to return (default 5).",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
            handler=lambda args: perform_web_search(
                query=args.get("query", ""),
                max_results=int(args.get("max_results", 5)),
            ),
        )

        self.register_tool(
            name="scrape_url",
            description="Extracts clean, readable text content from a web URL, filtering boilerplate HTML.",
            input_schema={
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "Full target URL to fetch and parse.",
                    },
                    "max_length": {
                        "type": "integer",
                        "description": "Character limit for returned body text (default 2500).",
                        "default": 2500,
                    },
                },
                "required": ["url"],
            },
            handler=lambda args: scrape_url_content(
                url=args.get("url", ""),
                max_length=int(args.get("max_length", 2500)),
            ),
        )

        self.register_tool(
            name="vector_search",
            description="Searches indexed research documents and snippets semantically using vector similarity (ChromaDB).",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Semantic search query to retrieve relevant contextual passages.",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of top matching passages to return (default 4).",
                        "default": 4,
                    },
                },
                "required": ["query"],
            },
            handler=lambda args: search_vector_store(
                query=args.get("query", ""),
                top_k=int(args.get("top_k", 4)),
            ),
        )

        self.register_tool(
            name="index_document",
            description="Indexes a document or text snippet into the vector store for semantic retrieval.",
            input_schema={
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text body or passage to index.",
                    },
                    "title": {
                        "type": "string",
                        "description": "Title or label for the source document.",
                        "default": "",
                    },
                    "url": {
                        "type": "string",
                        "description": "Source URL or identifier.",
                        "default": "",
                    },
                    "doc_id": {
                        "type": "string",
                        "description": "Unique identifier for the document chunk.",
                        "default": "",
                    },
                },
                "required": ["text"],
            },
            handler=lambda args: index_document(
                text=args.get("text", ""),
                title=args.get("title", ""),
                url=args.get("url", ""),
                doc_id=args.get("doc_id", ""),
            ),
        )

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable[[Dict[str, Any]], Any],
    ) -> None:
        """Register an MCP tool definition and its execution handler."""
        self._tools[name] = {
            "name": name,
            "description": description,
            "inputSchema": input_schema,
        }
        self._handlers[name] = handler

    def list_tools(self) -> List[Dict[str, Any]]:
        """Return the standard MCP tool catalog for tools/list."""
        return list(self._tools.values())

    def call_tool(self, name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool conforming to the MCP tools/call standard."""
        if name not in self._handlers:
            return {
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": f"Error: Tool '{name}' not found on MCP server '{self.server_name}'",
                    }
                ],
            }

        try:
            handler = self._handlers[name]
            result = handler(arguments)
            return {
                "isError": False,
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, ensure_ascii=False) if not isinstance(result, str) else result,
                    }
                ],
                "raw_result": result,
            }
        except Exception as exc:
            logger.exception(f"MCP tool execution failed: {name}")
            return {
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": f"Execution Error in {name}: {str(exc)}",
                    }
                ],
            }

    def handle_json_rpc(self, request_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle standard JSON-RPC 2.0 MCP requests."""
        req_id = request_payload.get("id")
        method = request_payload.get("method", "")
        params = request_payload.get("params", {})

        if method == "tools/list":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": self.list_tools()},
            }
        elif method == "tools/call":
            tool_name = params.get("name", "")
            tool_args = params.get("arguments", {})
            call_res = self.call_tool(tool_name, tool_args)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": call_res,
            }
        elif method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "serverInfo": {"name": self.server_name, "version": self.version},
                    "capabilities": {"tools": {}},
                },
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method '{method}' not found"},
            }

    def run_stdio(self) -> None:
        """Run MCP server over standard input/output for CLI/IDE integrations."""
        for line in sys.stdin:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
                response = self.handle_json_rpc(payload)
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
            except Exception as err:
                err_resp = {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {str(err)}"},
                }
                sys.stdout.write(json.dumps(err_resp) + "\n")
                sys.stdout.flush()


# Global shared in-process instance
_mcp_server: Optional[ResearchMCPServer] = None


def get_mcp_server() -> ResearchMCPServer:
    """Get or create singleton MCP server instance."""
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = ResearchMCPServer()
    return _mcp_server


if __name__ == "__main__":
    server = ResearchMCPServer()
    server.run_stdio()
