"""Tests for Model Context Protocol (MCP) Server and Tools."""
from __future__ import annotations

import json
import unittest
from src.mcp.client import MCPClient
from src.mcp.server import ResearchMCPServer


class TestResearchMCPServer(unittest.TestCase):
    """Test suite validating standard Model Context Protocol compliance."""

    def setUp(self) -> None:
        self.server = ResearchMCPServer(server_name="test-mcp-server")
        self.client = MCPClient(server=self.server)

    def test_registered_tools_catalog(self) -> None:
        tools = self.server.list_tools()
        tool_names = [t["name"] for t in tools]
        self.assertIn("web_search", tool_names)
        self.assertIn("scrape_url", tool_names)
        self.assertIn("vector_search", tool_names)
        self.assertIn("index_document", tool_names)

    def test_llm_tool_schema_conversion(self) -> None:
        llm_tools = self.client.get_tools_for_llm()
        self.assertTrue(len(llm_tools) >= 4)
        for t in llm_tools:
            self.assertEqual(t["type"], "function")
            self.assertIn("name", t["function"])
            self.assertIn("parameters", t["function"])

    def test_mcp_json_rpc_tools_list(self) -> None:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        }
        res = self.server.handle_json_rpc(payload)
        self.assertEqual(res["jsonrpc"], "2.0")
        self.assertEqual(res["id"], 1)
        self.assertIn("tools", res["result"])

    def test_mcp_json_rpc_tool_call(self) -> None:
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "index_document",
                "arguments": {
                    "text": "Model Context Protocol standardizes agent tool integration.",
                    "title": "MCP Guide",
                },
            },
        }
        res = self.server.handle_json_rpc(payload)
        self.assertEqual(res["id"], 2)
        call_res = res["result"]
        self.assertFalse(call_res["isError"])


if __name__ == "__main__":
    unittest.main()
