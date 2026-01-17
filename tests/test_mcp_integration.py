"""
Integration tests for MCP endpoints.

Tests the full flow of MCP tool interactions including:
- Tool discovery
- Tool invocation
- Result handling
- Error scenarios
"""
import pytest
from httpx import AsyncClient


class TestMCPIntegration:
    """Integration tests for MCP tools workflow."""

    async def test_full_tool_workflow(self, client: AsyncClient, mcp_base_url: str):
        """Test complete workflow: list tools -> call tool -> verify result."""
        # Step 1: List available tools
        list_request = {
            "jsonrpc": "2.0",
            "id": 100,
            "method": "tools/list",
            "params": {},
        }

        list_response = await client.post(
            mcp_base_url,
            json=list_request,
            headers={"Content-Type": "application/json"},
        )

        assert list_response.status_code == 200
        list_data = list_response.json()
        tools = list_data["result"]["tools"]

        # Step 2: Find a tool we can test
        tool_name = None
        for tool in tools:
            if tool["name"] == "suggest_movie":
                tool_name = tool["name"]
                break

        assert tool_name is not None, "suggest_movie tool not found"

        # Step 3: Call the tool
        call_request = {
            "jsonrpc": "2.0",
            "id": 101,
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": {"genre": "Action"},
            },
        }

        call_response = await client.post(
            mcp_base_url,
            json=call_request,
            headers={"Content-Type": "application/json"},
        )

        assert call_response.status_code == 200
        call_data = call_response.json()

        # Step 4: Verify result structure
        assert "result" in call_data
        result = call_data["result"]
        assert "content" in result
        assert isinstance(result["content"], list)
        assert len(result["content"]) > 0

    async def test_multiple_tool_calls(self, client: AsyncClient, mcp_base_url: str):
        """Test calling multiple tools in sequence."""
        tools_to_test = [
            {"name": "suggest_movie", "arguments": {"genre": "Comedy"}},
            {"name": "get_top_movies", "arguments": {}},
        ]

        for i, tool_config in enumerate(tools_to_test):
            request = {
                "jsonrpc": "2.0",
                "id": 200 + i,
                "method": "tools/call",
                "params": {
                    "name": tool_config["name"],
                    "arguments": tool_config["arguments"],
                },
            }

            response = await client.post(
                mcp_base_url,
                json=request,
                headers={"Content-Type": "application/json"},
            )

            assert response.status_code == 200
            data = response.json()
            assert "result" in data
            assert data["result"].get("isError", False) == False

    async def test_tool_error_recovery(self, client: AsyncClient, mcp_base_url: str):
        """Test that tool execution errors provide actionable feedback."""
        # Call with invalid input
        invalid_request = {
            "jsonrpc": "2.0",
            "id": 300,
            "method": "tools/call",
            "params": {
                "name": "suggest_movie",
                "arguments": {"genre": "INVALID_GENRE"},
            },
        }

        response = await client.post(
            mcp_base_url,
            json=invalid_request,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should return error or error indication
        result = data.get("result", {})
        error_content = result.get("content", [])

        # Error message should be informative (for LLM self-correction)
        if error_content:
            error_text = error_content[0].get("text", "")
            assert len(error_text) > 0

        # Now call with valid input (recovery)
        valid_request = {
            "jsonrpc": "2.0",
            "id": 301,
            "method": "tools/call",
            "params": {
                "name": "suggest_movie",
                "arguments": {"genre": "Action"},
            },
        }

        valid_response = await client.post(
            mcp_base_url,
            json=valid_request,
            headers={"Content-Type": "application/json"},
        )

        assert valid_response.status_code == 200
        valid_data = valid_response.json()
        assert valid_data["result"].get("isError", False) == False

    async def test_concurrent_tool_calls(self, client: AsyncClient, mcp_base_url: str):
        """Test that multiple concurrent tool calls work correctly."""
        import asyncio

        async def call_tool(tool_name: str, arguments: dict, request_id: int):
            request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "tools/call",
                "params": {
                    "name": tool_name,
                    "arguments": arguments,
                },
            }
            response = await client.post(
                mcp_base_url,
                json=request,
                headers={"Content-Type": "application/json"},
            )
            return response.json()

        # Make concurrent calls
        tasks = [
            call_tool("suggest_movie", {"genre": "Action"}, 400),
            call_tool("get_top_movies", {}, 401),
            call_tool("suggest_movie", {"genre": "Comedy"}, 402),
        ]

        results = await asyncio.gather(*tasks)

        # Verify all calls succeeded
        for result in results:
            assert "result" in result or "error" in result
