"""MCP (Model Context Protocol) client implementation."""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Union
from urllib.parse import urljoin
import httpx
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)


class MCPTool(BaseModel):
    """Model for MCP tool definition."""
    name: str
    description: str
    inputSchema: Dict[str, Any]


class MCPResource(BaseModel):
    """Model for MCP resource definition."""
    uri: str
    name: str
    description: str
    mimeType: str


class MCPClient:
    """Async MCP client for connecting to MCP servers."""
    
    def __init__(
        self,
        server_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        """Initialize MCP client."""
        self.server_url = server_url or settings.mcp_server_url
        self.api_key = api_key or settings.mcp_api_key
        self.timeout = timeout or settings.mcp_timeout
        self._client: Optional[httpx.AsyncClient] = None
        self._session_id: Optional[str] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def connect(self):
        """Establish connection to MCP server."""
        try:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            self._client = httpx.AsyncClient(
                base_url=self.server_url,
                headers=headers,
                timeout=self.timeout
            )
            
            # Test connection
            await self._test_connection()
            logger.info(f"Connected to MCP server at {self.server_url}")
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server: {e}")
            raise
    
    async def close(self):
        """Close MCP connection."""
        if self._client:
            await self._client.aclose()
            self._client = None
            logger.info("MCP connection closed")
    
    async def _test_connection(self):
        """Test the connection to the MCP server."""
        if not self._client:
            await self.connect()
        
        response = await self._client.get("/health")
        response.raise_for_status()
        data = await response.json()
        
        if data.get("status") != "ok":
            raise ConnectionError("MCP server is not healthy")
    
    async def list_tools(self) -> List[MCPTool]:
        """List available tools from the MCP server."""
        if not self._client:
            await self.connect()
        
        try:
            response = await self._client.get("/tools")
            response.raise_for_status()
            
            tools_data = await response.json()
            return [MCPTool(**tool) for tool in tools_data.get("tools", [])]
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to list tools: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing tools: {e}")
            raise
    
    async def call_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout: Optional[int] = None
    ) -> Dict[str, Any]:
        """Call a tool on the MCP server."""
        if not self._client:
            await self.connect()
        
        try:
            payload = {
                "tool": tool_name,
                "arguments": arguments
            }
            
            response = await self._client.post(
                "/tools/call",
                json=payload,
                timeout=timeout or self.timeout
            )
            response.raise_for_status()
            
            result = await response.json()
            logger.info(f"Tool {tool_name} called successfully")
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to call tool {tool_name}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling tool {tool_name}: {e}")
            raise
    
    async def list_resources(self) -> List[MCPResource]:
        """List available resources from the MCP server."""
        if not self._client:
            await self.connect()
        
        try:
            response = await self._client.get("/resources")
            response.raise_for_status()
            
            resources_data = await response.json()
            return [MCPResource(**resource) for resource in resources_data.get("resources", [])]
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to list resources: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error listing resources: {e}")
            raise
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Read a resource from the MCP server."""
        if not self._client:
            await self.connect()
        
        try:
            response = await self._client.get(f"/resources/read", params={"uri": uri})
            response.raise_for_status()
            
            result = await response.json()
            logger.info(f"Resource {uri} read successfully")
            return result
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to read resource {uri}: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error reading resource {uri}: {e}")
            raise
    
    async def get_server_info(self) -> Dict[str, Any]:
        """Get information about the MCP server."""
        if not self._client:
            await self.connect()
        
        try:
            response = await self._client.get("/info")
            response.raise_for_status()
            
            return await response.json()
            
        except httpx.HTTPError as e:
            logger.error(f"Failed to get server info: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error getting server info: {e}")
            raise
    
    async def ping(self) -> bool:
        """Ping the MCP server to check for a connection."""
        try:
            await self._test_connection()
            return True
        except Exception as e:
            logger.error(f"Ping failed: {e}")
            return False


class MockMCPClient:
    """Mock MCP client for testing and development."""
    
    def __init__(self):
        self.tools = [
            MCPTool(
                name="search_web",
                description="Search the web for information",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"}
                    },
                    "required": ["query"]
                }
            ),
            MCPTool(
                name="analyze_text",
                description="Analyze text content",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "text": {"type": "string", "description": "Text to analyze"},
                        "analysis_type": {"type": "string", "enum": ["sentiment", "summary", "keywords"]}
                    },
                    "required": ["text"]
                }
            )
        ]
        
        self.resources = [
            MCPResource(
                uri="file:///example.txt",
                name="Example File",
                description="An example text file",
                mimeType="text/plain"
            )
        ]
    
    async def connect(self):
        """Mock connection."""
        logger.info("Mock MCP client connected")
    
    async def close(self):
        """Mock close."""
        logger.info("Mock MCP client closed")
    
    async def list_tools(self) -> List[MCPTool]:
        """List mock tools."""
        return self.tools
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Mock tool call."""
        if tool_name == "search_web":
            return {
                "result": f"Mock search results for: {arguments.get('query', '')}",
                "sources": ["mock_source_1", "mock_source_2"]
            }
        elif tool_name == "analyze_text":
            return {
                "result": f"Mock analysis of text: {arguments.get('text', '')[:50]}...",
                "analysis_type": arguments.get("analysis_type", "summary")
            }
        else:
            raise ValueError(f"Unknown tool: {tool_name}")
    
    async def list_resources(self) -> List[MCPResource]:
        """List mock resources."""
        return self.resources
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """Mock resource read."""
        return {
            "content": f"Mock content for {uri}",
            "mimeType": "text/plain"
        }
    
    async def get_server_info(self) -> Dict[str, Any]:
        """Get mock server info."""
        return {
            "name": "Mock MCP Server",
            "version": "1.0.0",
            "capabilities": ["tools", "resources"]
        }
    
    async def ping(self) -> bool:
        """Mock ping."""
        return True


# Global client instance
mcp_client = MCPClient() 