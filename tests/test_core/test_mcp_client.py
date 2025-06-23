"""Tests for MCP client functionality."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.core.mcp_client import MCPClient, MCPTool, MCPResource


@pytest.fixture
def mcp_client():
    """Provides a fresh MCPClient instance for each test."""
    return MCPClient(server_url="http://test-mcp-server:8080", api_key="test-key")


class TestMCPClient:
    """Test suite for the asynchronous MCPClient."""

    @pytest.mark.asyncio
    async def test_connect_success(self, mcp_client):
        """Test successful connection to the MCP server."""
        with patch('httpx.AsyncClient') as mock_async_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json = AsyncMock(return_value={"status": "ok"})
            mock_client.get.return_value = mock_response
            mock_async_client_class.return_value = mock_client

            await mcp_client.connect()
            mock_client.get.assert_called_once_with("/health")

    @pytest.mark.asyncio
    async def test_connect_failure(self, mcp_client):
        """Test connection failure when the server is unhealthy."""
        with patch('httpx.AsyncClient') as mock_async_client_class:
            mock_client = AsyncMock()
            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json = AsyncMock(return_value={"status": "unhealthy"})
            mock_client.get.return_value = mock_response
            mock_async_client_class.return_value = mock_client

            with pytest.raises(ConnectionError, match="MCP server is not healthy"):
                await mcp_client.connect()

    @pytest.mark.asyncio
    async def test_list_tools(self, mcp_client):
        """Test listing available tools."""
        with patch.object(mcp_client, '_client', new_callable=AsyncMock) as mock_client:
            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json = AsyncMock(return_value={
                "tools": [{"name": "tool1", "description": "A test tool", "inputSchema": {}}]
            })
            mock_client.get.return_value = mock_response

            tools = await mcp_client.list_tools()

            mock_client.get.assert_called_once_with("/tools")
            assert len(tools) == 1
            assert isinstance(tools[0], MCPTool)
            assert tools[0].name == "tool1"

    @pytest.mark.asyncio
    async def test_call_tool(self, mcp_client):
        """Test calling a specific tool."""
        with patch.object(mcp_client, '_client', new_callable=AsyncMock) as mock_client:
            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json = AsyncMock(return_value={"result": "success"})
            mock_client.post.return_value = mock_response

            result = await mcp_client.call_tool("tool1", {"arg": "value"})

            expected_payload = {"tool": "tool1", "arguments": {"arg": "value"}}
            mock_client.post.assert_called_once_with(
                "/tools/call", json=expected_payload, timeout=mcp_client.timeout
            )
            assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_list_resources(self, mcp_client: MCPClient):
        """Test listing available resources."""
        with patch.object(mcp_client, '_client', new_callable=AsyncMock) as mock_client:
            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json = AsyncMock(return_value={
                "resources": [{"uri": "file:///test.txt", "name": "Test", "description": "", "mimeType": "text/plain"}]
            })
            mock_client.get.return_value = mock_response

            resources = await mcp_client.list_resources()

            mock_client.get.assert_called_once_with("/resources")
            assert len(resources) == 1
            assert isinstance(resources[0], MCPResource)

    @pytest.mark.asyncio
    async def test_read_resource(self, mcp_client: MCPClient):
        """Test reading a specific resource."""
        with patch.object(mcp_client, '_client', new_callable=AsyncMock) as mock_client:
            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json = AsyncMock(return_value={"content": "hello"})
            mock_client.get.return_value = mock_response

            uri = "file:///test.txt"
            resource_content = await mcp_client.read_resource(uri)

            mock_client.get.assert_called_once_with(f"/resources/read", params={"uri": uri})
            assert resource_content["content"] == "hello"

    @pytest.mark.asyncio
    async def test_get_server_info(self, mcp_client: MCPClient):
        """Test getting server information."""
        with patch.object(mcp_client, '_client', new_callable=AsyncMock) as mock_client:
            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock()
            mock_response.json = AsyncMock(return_value={"name": "Test MCP Server"})
            mock_client.get.return_value = mock_response

            info = await mcp_client.get_server_info()

            mock_client.get.assert_called_once_with("/info")
            assert info["name"] == "Test MCP Server"

    @pytest.mark.asyncio
    async def test_ping(self, mcp_client: MCPClient):
        """Test pinging the server."""
        with patch.object(mcp_client, '_test_connection', new_callable=AsyncMock) as mock_test_conn:
            result = await mcp_client.ping()
            mock_test_conn.assert_called_once()
            assert result is True

        with patch.object(mcp_client, '_test_connection', new_callable=AsyncMock) as mock_test_conn:
            mock_test_conn.side_effect = Exception("Ping Failed")
            result = await mcp_client.ping()
            assert result is False