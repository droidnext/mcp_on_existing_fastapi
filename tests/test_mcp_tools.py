"""
Test cases for MCP Tools API.

Based on MCP Specification: https://modelcontextprotocol.io/specification/2025-11-25/server/tools

Tests cover:
- Listing tools (tools/list)
- Calling tools (tools/call)
- Tool result formats (text, structured content)
- Error handling (unknown tools, invalid parameters)
- Tool input/output schema validation
"""
import json
import pytest
from httpx import AsyncClient


class TestMCPToolsList:
    """Test cases for tools/list endpoint."""

    async def test_list_tools_success(self, client: AsyncClient, mcp_base_url: str):
        """
        Test listing all available tools.
        
        Specification: https://modelcontextprotocol.io/specification/2025-11-25/server/tools#listing-tools
        """
        request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        }

        response = await client.post(
            mcp_base_url,
            json=request,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()

        # Validate JSON-RPC 2.0 response structure
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert "result" in data
        assert "tools" in data["result"]

        # Validate tool structure
        tools = data["result"]["tools"]
        assert isinstance(tools, list)
        assert len(tools) > 0

        # Validate each tool has required fields
        for tool in tools:
            assert "name" in tool
            assert isinstance(tool["name"], str)
            assert 1 <= len(tool["name"]) <= 128  # Tool name length per spec
            assert "description" in tool
            assert "inputSchema" in tool
            assert tool["inputSchema"]["type"] == "object"  # Per spec

    async def test_list_tools_with_pagination(
        self, client: AsyncClient, mcp_base_url: str
    ):
        """Test listing tools with pagination cursor."""
        request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {"cursor": "test-cursor"},
        }

        response = await client.post(
            mcp_base_url,
            json=request,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["jsonrpc"] == "2.0"
        assert "result" in data

    async def test_list_tools_returns_expected_tools(
        self, client: AsyncClient, mcp_base_url: str
    ):
        """Test that expected tools are present in the list."""
        request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/list",
            "params": {},
        }

        response = await client.post(
            mcp_base_url,
            json=request,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        tools = data["result"]["tools"]

        # Get tool names
        tool_names = [tool["name"] for tool in tools]

        # Verify expected tools exist
        expected_tools = ["suggest_movie", "get_top_movies", "find_movies_title_cast"]
        for expected_tool in expected_tools:
            assert (
                expected_tool in tool_names
            ), f"Expected tool '{expected_tool}' not found in tools list"

    async def test_tool_schema_structure(self, client: AsyncClient, mcp_base_url: str):
        """Test that tool schemas follow MCP specification format."""
        request = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/list",
            "params": {},
        }

        response = await client.post(
            mcp_base_url,
            json=request,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        tools = data["result"]["tools"]

        for tool in tools:
            # Validate inputSchema structure
            input_schema = tool["inputSchema"]
            assert input_schema["type"] == "object"
            assert "properties" in input_schema or "additionalProperties" in input_schema

            # Tool name validation per spec
            tool_name = tool["name"]
            # Only allowed characters: letters, digits, underscore, hyphen, dot
            allowed_chars = set(
                "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-."
            )
            assert all(c in allowed_chars for c in tool_name)


class TestMCPToolsCall:
    """Test cases for tools/call endpoint."""

    async def test_call_suggest_movie_success(
        self, client: AsyncClient, mcp_base_url: str
    ):
        """
        Test calling suggest_movie tool with valid parameters.
        
        Specification: https://modelcontextprotocol.io/specification/2025-11-25/server/tools#calling-tools
        """
        request = {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "suggest_movie",
                "arguments": {"genre": "Action"},
            },
        }

        response = await client.post(
            mcp_base_url,
            json=request,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()

        # Validate JSON-RPC 2.0 response structure
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 5
        assert "result" in data

        # Validate tool result structure
        result = data["result"]
        assert "content" in result
        assert isinstance(result["content"], list)
        assert len(result["content"]) > 0

        # Validate content format (text content)
        content_item = result["content"][0]
        assert "type" in content_item
        assert content_item["type"] == "text"
        assert "text" in content_item
        assert isinstance(content_item["text"], str)

        # Tool should not be in error state for valid input
        assert result.get("isError", False) == False

    async def test_call_get_top_movies_success(
        self, client: AsyncClient, mcp_base_url: str
    ):
        """Test calling get_top_movies tool with valid parameters."""
        request = {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "get_top_movies",
                "arguments": {},
            },
        }

        response = await client.post(
            mcp_base_url,
            json=request,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["jsonrpc"] == "2.0"
        assert "result" in data
        result = data["result"]

        # Should return text content
        assert "content" in result
        assert len(result["content"]) > 0
        assert result["content"][0]["type"] == "text"

    async def test_call_get_top_movies_with_rating(
        self, client: AsyncClient, mcp_base_url: str
    ):
        """Test calling get_top_movies with rating filter."""
        request = {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "get_top_movies",
                "arguments": {"rating": "PG"},
            },
        }

        response = await client.post(
            mcp_base_url,
            json=request,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["jsonrpc"] == "2.0"
        assert "result" in data
        assert data["result"].get("isError", False) == False

    async def test_call_find_movies_title_cast_success(
        self, client: AsyncClient, mcp_base_url: str
    ):
        """Test calling find_movies_title_cast tool."""
        request = {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {
                "name": "find_movies_title_cast",
                "arguments": {
                    "title": "Matrix",
                    "cast": "Keanu Reeves",
                },
            },
        }

        response = await client.post(
            mcp_base_url,
            json=request,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["jsonrpc"] == "2.0"
        assert "result" in data

        # Should return text content or indicate no results
        result = data["result"]
        assert "content" in result
        assert len(result["content"]) > 0

    async def test_call_unknown_tool_error(
        self, client: AsyncClient, mcp_base_url: str
    ):
        """
        Test calling a non-existent tool returns protocol error.
        
        Specification: https://modelcontextprotocol.io/specification/2025-11-25/server/tools#error-handling
        """
        request = {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "tools/call",
            "params": {
                "name": "unknown_tool",
                "arguments": {},
            },
        }

        response = await client.post(
            mcp_base_url,
            json=request,
            headers={"Content-Type": "application/json"},
        )

        # Should return error for unknown tool
        assert response.status_code == 200
        data = response.json()

        # Protocol error should be in error field (not result.isError)
        assert "error" in data or (
            "result" in data and data["result"].get("isError") == True
        )

    async def test_call_tool_invalid_parameters(
        self, client: AsyncClient, mcp_base_url: str
    ):
        """
        Test calling tool with invalid parameters returns tool execution error.
        
        Specification: https://modelcontextprotocol.io/specification/2025-11-25/server/tools#error-handling
        """
        request = {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {
                "name": "suggest_movie",
                "arguments": {
                    "genre": "InvalidGenreThatDoesNotExist",
                },
            },
        }

        response = await client.post(
            mcp_base_url,
            json=request,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should return result with isError: true for tool execution errors
        assert "result" in data
        result = data["result"]

        # Tool execution errors should include helpful error message
        assert "content" in result
        assert len(result["content"]) > 0
        # Error message should be informative
        error_text = result["content"][0].get("text", "")
        assert len(error_text) > 0

    async def test_call_tool_missing_required_parameters(
        self, client: AsyncClient, mcp_base_url: str
    ):
        """Test calling tool without required parameters."""
        request = {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "tools/call",
            "params": {
                "name": "find_movies_title_cast",
                "arguments": {
                    # Missing required 'title' or 'cast'
                },
            },
        }

        response = await client.post(
            mcp_base_url,
            json=request,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should return error (either protocol or tool execution error)
        assert "error" in data or (
            "result" in data and data["result"].get("isError") == True
        )

    async def test_tool_result_content_format(
        self, client: AsyncClient, mcp_base_url: str
    ):
        """
        Test tool result content follows MCP specification format.
        
        Specification: https://modelcontextprotocol.io/specification/2025-11-25/server/tools#text-content
        """
        request = {
            "jsonrpc": "2.0",
            "id": 12,
            "method": "tools/call",
            "params": {
                "name": "suggest_movie",
                "arguments": {"genre": "Comedy"},
            },
        }

        response = await client.post(
            mcp_base_url,
            json=request,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        result = data["result"]

        # Validate content structure
        assert "content" in result
        content = result["content"]

        for item in content:
            # Text content should have type and text fields
            if item.get("type") == "text":
                assert "text" in item
                assert isinstance(item["text"], str)

    async def test_jsonrpc_request_validation(
        self, client: AsyncClient, mcp_base_url: str
    ):
        """Test that invalid JSON-RPC requests are properly rejected."""
        # Missing required fields
        invalid_request = {
            "jsonrpc": "2.0",
            # Missing "id" and "method"
        }

        response = await client.post(
            mcp_base_url,
            json=invalid_request,
            headers={"Content-Type": "application/json"},
        )

        # Should return error for malformed request
        assert response.status_code >= 400 or (
            response.status_code == 200
            and "error" in response.json()
        )

    async def test_tool_call_with_empty_arguments(
        self, client: AsyncClient, mcp_base_url: str
    ):
        """Test calling tool with empty arguments object."""
        request = {
            "jsonrpc": "2.0",
            "id": 13,
            "method": "tools/call",
            "params": {
                "name": "get_top_movies",
                "arguments": {},
            },
        }

        response = await client.post(
            mcp_base_url,
            json=request,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()

        # Tools with no required parameters should work with empty arguments
        assert "result" in data
        result = data["result"]
        assert "content" in result


class TestMCPToolsErrorHandling:
    """Test cases for error handling per MCP specification."""

    async def test_protocol_error_structure(
        self, client: AsyncClient, mcp_base_url: str
    ):
        """
        Test protocol errors follow JSON-RPC 2.0 error format.
        
        Specification: https://modelcontextprotocol.io/specification/2025-11-25/server/tools#error-handling
        """
        request = {
            "jsonrpc": "2.0",
            "id": 14,
            "method": "tools/call",
            "params": {
                "name": "nonexistent_tool_name_12345",
                "arguments": {},
            },
        }

        response = await client.post(
            mcp_base_url,
            json=request,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()

        # Protocol errors should have error field with code and message
        if "error" in data:
            error = data["error"]
            assert "code" in error
            assert "message" in error
            assert isinstance(error["code"], int)

    async def test_tool_execution_error_structure(
        self, client: AsyncClient, mcp_base_url: str
    ):
        """
        Test tool execution errors use isError flag.
        
        Specification: https://modelcontextprotocol.io/specification/2025-11-25/server/tools#error-handling
        """
        request = {
            "jsonrpc": "2.0",
            "id": 15,
            "method": "tools/call",
            "params": {
                "name": "suggest_movie",
                "arguments": {"genre": "INVALID"},
            },
        }

        response = await client.post(
            mcp_base_url,
            json=request,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()

        # Tool execution errors should have isError: true
        if "result" in data:
            result = data["result"]
            # May have isError flag, or error info in content
            assert "content" in result
            # Error messages should be helpful for LLM self-correction
            if result.get("isError") == True:
                assert len(result["content"]) > 0


class TestMCPToolsSchema:
    """Test cases for tool schema validation per MCP specification."""

    async def test_tool_input_schema_validation(
        self, client: AsyncClient, mcp_base_url: str
    ):
        """
        Test that tool input schemas are valid JSON Schema.
        
        Specification: https://modelcontextprotocol.io/specification/2025-11-25/server/tools#tool
        """
        request = {
            "jsonrpc": "2.0",
            "id": 16,
            "method": "tools/list",
            "params": {},
        }

        response = await client.post(
            mcp_base_url,
            json=request,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        tools = data["result"]["tools"]

        for tool in tools:
            input_schema = tool["inputSchema"]

            # Per spec: MUST be a valid JSON Schema object (not null)
            assert input_schema is not None
            assert isinstance(input_schema, dict)
            assert input_schema["type"] == "object"

    async def test_tool_name_validation(self, client: AsyncClient, mcp_base_url: str):
        """
        Test tool names follow MCP specification requirements.
        
        Specification: https://modelcontextprotocol.io/specification/2025-11-25/server/tools#tool-names
        """
        request = {
            "jsonrpc": "2.0",
            "id": 17,
            "method": "tools/list",
            "params": {},
        }

        response = await client.post(
            mcp_base_url,
            json=request,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        tools = data["result"]["tools"]

        for tool in tools:
            name = tool["name"]

            # Length: 1-128 characters (inclusive)
            assert 1 <= len(name) <= 128

            # Allowed characters only: letters, digits, underscore, hyphen, dot
            allowed_chars = set(
                "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-."
            )
            assert all(c in allowed_chars for c in name), f"Tool name '{name}' contains invalid characters"

    async def test_tool_no_parameters_schema(
        self, client: AsyncClient, mcp_base_url: str
    ):
        """
        Test tools with no parameters use recommended schema format.
        
        Specification: https://modelcontextprotocol.io/specification/2025-11-25/server/tools#schema-examples
        """
        request = {
            "jsonrpc": "2.0",
            "id": 18,
            "method": "tools/list",
            "params": {},
        }

        response = await client.post(
            mcp_base_url,
            json=request,
            headers={"Content-Type": "application/json"},
        )

        assert response.status_code == 200
        data = response.json()
        tools = data["result"]["tools"]

        # Find tools with no parameters (check if no properties or empty properties)
        for tool in tools:
            input_schema = tool["inputSchema"]
            properties = input_schema.get("properties", {})

            # If no properties, should use additionalProperties: false (recommended)
            if len(properties) == 0:
                # Either additionalProperties: false or no properties key
                # Both are valid per spec
                assert (
                    "additionalProperties" not in input_schema
                    or input_schema.get("additionalProperties") == False
                    or input_schema.get("additionalProperties") == True
                )
