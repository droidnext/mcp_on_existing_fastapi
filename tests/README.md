# MCP Tools Test Suite

This directory contains comprehensive tests for the MCP (Model Context Protocol) Tools API implementation.

## Test Coverage

Tests are organized by functionality and cover the MCP Tools specification: https://modelcontextprotocol.io/specification/2025-11-25/server/tools

### Test Files

1. **`test_mcp_tools.py`** - Core MCP tools functionality tests
   - Tool listing (`tools/list`)
   - Tool invocation (`tools/call`)
   - Tool result formats
   - Error handling
   - Schema validation

2. **`test_mcp_integration.py`** - Integration tests
   - End-to-end workflows
   - Multiple tool calls
   - Error recovery scenarios
   - Concurrent operations

3. **`test_jwt.py`** - JWT authentication tests (existing)

### Test Categories

#### TestMCPToolsList
- `test_list_tools_success` - Basic tool listing
- `test_list_tools_with_pagination` - Pagination support
- `test_list_tools_returns_expected_tools` - Tool discovery
- `test_tool_schema_structure` - Schema validation

#### TestMCPToolsCall
- `test_call_suggest_movie_success` - Valid tool call
- `test_call_get_top_movies_success` - Tool with optional parameters
- `test_call_find_movies_title_cast_success` - Multi-parameter tool
- `test_call_unknown_tool_error` - Protocol error handling
- `test_call_tool_invalid_parameters` - Tool execution error handling
- `test_call_tool_missing_required_parameters` - Parameter validation
- `test_tool_result_content_format` - Result format validation

#### TestMCPToolsErrorHandling
- `test_protocol_error_structure` - JSON-RPC 2.0 error format
- `test_tool_execution_error_structure` - Tool-level error format

#### TestMCPToolsSchema
- `test_tool_input_schema_validation` - JSON Schema validation
- `test_tool_name_validation` - Tool name format per spec
- `test_tool_no_parameters_schema` - Schema for parameterless tools

## Running Tests

### Run all MCP tests
```bash
pytest tests/test_mcp_tools.py tests/test_mcp_integration.py -v
```

### Run specific test class
```bash
pytest tests/test_mcp_tools.py::TestMCPToolsList -v
```

### Run specific test
```bash
pytest tests/test_mcp_tools.py::TestMCPToolsCall::test_call_suggest_movie_success -v
```

### Run with coverage
```bash
pytest tests/ --cov=app --cov-report=html
```

## Test Configuration

Tests use the `conftest.py` file for shared fixtures:
- `client` - Async HTTP client for testing
- `mcp_base_url` - MCP endpoint base URL
- `valid_jsonrpc_request` - Helper for creating JSON-RPC requests

## MCP Specification Compliance

These tests verify compliance with the MCP Tools specification:

- ✅ **Protocol Messages**: `tools/list`, `tools/call`
- ✅ **Tool Structure**: name, description, inputSchema, outputSchema
- ✅ **Tool Names**: Format validation (1-128 chars, allowed characters)
- ✅ **Tool Results**: Text content, structured content, error handling
- ✅ **Error Handling**: Protocol errors vs. tool execution errors
- ✅ **Schema Validation**: JSON Schema format, parameter validation

## Notes

- Tests assume JWT authentication is disabled for testing (`ENABLE_JWT=false`)
- Tests use the `dev` environment configuration
- All tests use async/await for proper async handling
- Tests follow JSON-RPC 2.0 specification format

## References

- [MCP Tools Specification](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)
- [JSON-RPC 2.0 Specification](https://www.jsonrpc.org/specification)
