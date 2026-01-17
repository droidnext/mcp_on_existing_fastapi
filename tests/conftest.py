"""
Pytest configuration and fixtures for MCP tests.
"""
import os
import pytest
from httpx import AsyncClient
from app.main import app
from app.core.config import settings

# Set test environment
os.environ["APP_ENV"] = "dev"
os.environ["ENABLE_JWT"] = "false"


@pytest.fixture
async def client():
    """Create async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def mcp_base_url():
    """Get MCP base URL for testing."""
    return "/mcp"


@pytest.fixture
def valid_jsonrpc_request():
    """Factory fixture to create valid JSON-RPC 2.0 requests."""
    def _create_request(method: str, params: dict = None, request_id: int = 1):
        """Create a valid JSON-RPC 2.0 request."""
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
        }
        if params:
            request["params"] = params
        return request
    return _create_request
