"""Tests for MCP client functionality."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.mcp_client import MCPClient, MockMCPClient, MCPTool, MCPResource


class TestMCPTool:
    """Test MCPTool model."""
    
    def test_mcp_tool_creation(self):
        """Test creating an MCPTool instance."""
        tool = MCPTool(
            name="test_tool",
            description="A test tool",
            inputSchema={"type": "object", "properties": {}}
        )
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.inputSchema == {"type": "object", "properties": {}}


class TestMCPResource:
    """Test MCPResource model."""
    
    def test_mcp_resource_creation(self):
        """Test creating an MCPResource instance."""
        resource = MCPResource(
            uri="file:///test.txt",
            name="Test File",
            description="A test file",
            mimeType="text/plain"
        )
        assert resource.uri == "file:///test.txt"
        assert resource.name == "Test File"
        assert resource.description == "A test file"
        assert resource.mimeType == "text/plain"


class TestMockMCPClient:
    """Test MockMCPClient functionality."""
    
    @pytest.fixture
    def mock_client(self):
        """Create a mock MCP client."""
        return MockMCPClient()
    
    @pytest.mark.asyncio
    async def test_mock_client_connect(self, mock_client):
        """Test mock client connection."""
        await mock_client.connect()
        # Should not raise any exceptions
    
    @pytest.mark.asyncio
    async def test_mock_client_close(self, mock_client):
        """Test mock client close."""
        await mock_client.close()
        # Should not raise any exceptions
    
    @pytest.mark.asyncio
    async def test_mock_client_list_tools(self, mock_client):
        """Test listing tools from mock client."""
        tools = await mock_client.list_tools()
        assert len(tools) == 2
        assert any(tool.name == "search_web" for tool in tools)
        assert any(tool.name == "analyze_text" for tool in tools)
    
    @pytest.mark.asyncio
    async def test_mock_client_call_tool_search(self, mock_client):
        """Test calling search_web tool."""
        result = await mock_client.call_tool("search_web", {"query": "test query"})
        assert "result" in result
        assert "sources" in result
        assert "test query" in result["result"]
    
    @pytest.mark.asyncio
    async def test_mock_client_call_tool_analyze(self, mock_client):
        """Test calling analyze_text tool."""
        result = await mock_client.call_tool("analyze_text", {"text": "test text", "analysis_type": "sentiment"})
        assert "result" in result
        assert "analysis_type" in result
        assert result["analysis_type"] == "sentiment"
    
    @pytest.mark.asyncio
    async def test_mock_client_call_unknown_tool(self, mock_client):
        """Test calling unknown tool raises error."""
        with pytest.raises(ValueError, match="Unknown tool: unknown_tool"):
            await mock_client.call_tool("unknown_tool", {})
    
    @pytest.mark.asyncio
    async def test_mock_client_list_resources(self, mock_client):
        """Test listing resources from mock client."""
        resources = await mock_client.list_resources()
        assert len(resources) == 1
        assert resources[0].uri == "file:///example.txt"
    
    @pytest.mark.asyncio
    async def test_mock_client_read_resource(self, mock_client):
        """Test reading resource from mock client."""
        result = await mock_client.read_resource("file:///example.txt")
        assert "content" in result
        assert "mimeType" in result
        assert result["mimeType"] == "text/plain"
    
    @pytest.mark.asyncio
    async def test_mock_client_get_server_info(self, mock_client):
        """Test getting server info from mock client."""
        info = await mock_client.get_server_info()
        assert "name" in info
        assert "version" in info
        assert "capabilities" in info
        assert info["name"] == "Mock MCP Server"
    
    @pytest.mark.asyncio
    async def test_mock_client_ping(self, mock_client):
        """Test ping functionality."""
        result = await mock_client.ping()
        assert result is True


@pytest.fixture
def mcp_client():
    """Create a clean MCP client instance for each test."""
    client = MCPClient(server_url="http://test-mcp-server:8080", api_key="test-key")
    client._client = None
    return client


@pytest.fixture
def mock_httpx_client():
    """Provides a sophisticated mock of httpx.AsyncClient."""
    mock_client = AsyncMock(spec=httpx.AsyncClient)

    async def mock_get(url, **kwargs):
        response = MagicMock(spec=httpx.Response)
        response.status_code = 200
        response.raise_for_status.return_value = None
        if url == "/health":
            response.json.return_value = {"status": "ok"}
        elif url == "/tools":
            response.json.return_value = [{"name": "tool1", "description": "A test tool"}]
        else:
            response.json.return_value = {}
        return response

    async def mock_post(url, **kwargs):
        response = MagicMock(spec=httpx.Response)
        response.status_code = 200
        response.raise_for_status.return_value = None
        response.json.return_value = {"result": "success"}
        return response

    mock_client.get.side_effect = mock_get
    mock_client.post.side_effect = mock_post
    return mock_client


class TestMCPClient:
    """Test MCP client functionality with robust mocking."""

    def test_mcp_client_initialization(self, mcp_client):
        """Test MCP client initialization."""
        assert mcp_client.server_url == "http://test-mcp-server:8080"
        assert mcp_client.api_key == "test-key"

    @pytest.mark.asyncio
    async def test_mcp_client_connect_success(self, mcp_client, mock_httpx_client):
        """Test successful connection to MCP server."""
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            await mcp_client.connect()
            mock_httpx_client.get.assert_called_once_with("/health")
            assert mcp_client._client is not None

    @pytest.mark.asyncio
    async def test_mcp_client_connect_with_api_key(self, mcp_client):
        """Test connection with API key in headers."""
        with patch('httpx.AsyncClient') as mock_async_client_class:
            mock_client_instance = AsyncMock()
            mock_client_instance.get.return_value.json.return_value = {"status": "ok"}
            mock_async_client_class.return_value = mock_client_instance

            await mcp_client.connect()
            call_kwargs = mock_async_client_class.call_args.kwargs
            assert call_kwargs['headers']['Authorization'] == f"Bearer {mcp_client.api_key}"

    @pytest.mark.asyncio
    async def test_mcp_client_connect_failure(self, mcp_client):
        """Test connection failure when server is not healthy."""
        mock_client = AsyncMock(spec=httpx.AsyncClient)
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.json.return_value = {"status": "unhealthy"} # Simulate unhealthy
        mock_client.get.return_value = mock_response
        
        with patch('httpx.AsyncClient', return_value=mock_client):
            with pytest.raises(ConnectionError, match="MCP server is not healthy"):
                await mcp_client.connect()
    
    @pytest.mark.asyncio
    async def test_mcp_client_close(self, mcp_client):
        """Test closing MCP client connection."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client_class.return_value = mock_client
            
            await mcp_client.connect()
            await mcp_client.close()
            
            mock_client.aclose.assert_called_once()
            assert mcp_client._client is None
    
    @pytest.mark.asyncio
    async def test_mcp_client_list_tools_success(self, mcp_client, mock_httpx_client):
        """Test successfully listing tools."""
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            tools = await mcp_client.list_tools()
            assert len(tools) == 1
            assert isinstance(tools[0], MCPTool)
            assert tools[0].name == "tool1"
            mock_httpx_client.get.assert_any_call("/tools")
    
    @pytest.mark.asyncio
    async def test_mcp_client_list_tools_failure(self, mcp_client):
        """Test tool listing failure."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()

            async def mock_get(url, **kwargs):
                if url == "/health":
                    # Successful health check
                    return MagicMock(raise_for_status=lambda: None)
                # Fail other calls
                raise httpx.HTTPError("Server error")

            mock_client.get.side_effect = mock_get
            mock_client_class.return_value = mock_client

            # Connect should succeed because health check is mocked to succeed
            await mcp_client.connect()

            # list_tools should fail because its GET call will raise an error
            with pytest.raises(httpx.HTTPError):
                await mcp_client.list_tools()
    
    @pytest.mark.asyncio
    async def test_mcp_client_call_tool_success(self, mcp_client, mock_httpx_client):
        """Test successfully calling a tool."""
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            result = await mcp_client.call_tool("tool1", {"arg": "value"})
            assert result == {"result": "success"}
            mock_httpx_client.post.assert_called_once_with(
                "/tools/tool1/call", json={"arguments": {"arg": "value"}}
            )
    
    @pytest.mark.asyncio
    async def test_mcp_client_call_tool_failure(self, mcp_client):
        """Test tool call failure."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.HTTPError("Tool call failed")
            mock_client_class.return_value = mock_client
            
            await mcp_client.connect()
            
            with pytest.raises(httpx.HTTPError):
                await mcp_client.call_tool("test_tool", {})
    
    @pytest.mark.asyncio
    async def test_mcp_client_list_resources_success(self, mcp_client):
        """Test successful resource listing."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {
                "resources": [
                    {
                        "uri": "file:///test.txt",
                        "name": "Test File",
                        "description": "A test file",
                        "mimeType": "text/plain"
                    }
                ]
            }
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            await mcp_client.connect()
            resources = await mcp_client.list_resources()
            
            assert len(resources) == 1
            assert resources[0].uri == "file:///test.txt"
    
    @pytest.mark.asyncio
    async def test_mcp_client_read_resource_success(self, mcp_client):
        """Test successful resource reading."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"content": "file content", "mimeType": "text/plain"}
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            await mcp_client.connect()
            result = await mcp_client.read_resource("file:///test.txt")
            
            assert result == {"content": "file content", "mimeType": "text/plain"}
    
    @pytest.mark.asyncio
    async def test_mcp_client_get_server_info_success(self, mcp_client):
        """Test successful server info retrieval."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"name": "Test Server", "version": "1.0.0"}
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            await mcp_client.connect()
            info = await mcp_client.get_server_info()
            
            assert info == {"name": "Test Server", "version": "1.0.0"}
    
    @pytest.mark.asyncio
    async def test_mcp_client_ping_success(self, mcp_client, mock_httpx_client):
        """Test successful ping."""
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            result = await mcp_client.ping()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_mcp_client_ping_failure(self, mcp_client):
        """Test ping failure."""
        # Mock the internal connection test to simulate failure
        with patch.object(mcp_client, "_test_connection", new=AsyncMock()) as mock_test:
            mock_test.side_effect = Exception("Connection failed")
            
            # Ping should catch the exception and return False
            result = await mcp_client.ping()
            assert result is False
    
    @pytest.mark.asyncio
    async def test_mcp_client_context_manager(self, mcp_client):
        """Test MCP client as context manager."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_response.json.return_value = {"status": "ok"}
            mock_client.get.return_value = mock_response
            mock_client_class.return_value = mock_client
            
            async with mcp_client:
                assert mcp_client._client is not None
            
            mock_client.aclose.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_mcp_client_auto_connect_on_operation(self, mcp_client, mock_httpx_client):
        """Test that client auto-connects when performing operations."""
        with patch('httpx.AsyncClient', return_value=mock_httpx_client):
            await mcp_client.ping()
            assert mcp_client._client is not None
            mock_httpx_client.get.assert_called_with("/health") 