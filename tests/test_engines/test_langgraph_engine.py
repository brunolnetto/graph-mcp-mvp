import pytest
from unittest.mock import AsyncMock
from app.engines.langgraph_engine import LangGraphEngine
from app.engines.schemas import LangGraphWorkflowConfig, LangGraphNodeConfig, LangGraphEdgeConfig

@pytest.mark.asyncio
async def test_happy_path():
    mcp_client = AsyncMock()
    mcp_client.call_tool = AsyncMock(side_effect=[{"result": 1}, {"result": 2}])
    engine = LangGraphEngine(mcp_client=mcp_client)
    config = {
        "nodes": [
            {"id": "n1", "tool": "toolA", "arguments": {}},
            {"id": "n2", "tool": "toolB", "arguments": {}}
        ],
        "edges": [
            {"from_node": "n1", "to_node": "n2"}
        ],
        "start_node": "n1"
    }
    result = await engine.execute(config)
    assert result["status"] == "completed"
    assert result["path"] == ["n1", "n2"]
    assert set(result["results"].keys()) == {"n1", "n2"}
    assert not result["errors"]

@pytest.mark.asyncio
async def test_branching():
    mcp_client = AsyncMock()
    mcp_client.call_tool = AsyncMock(side_effect=[{"result": 1}, {"result": 2}])
    engine = LangGraphEngine(mcp_client=mcp_client)
    config = {
        "nodes": [
            {"id": "n1", "tool": "toolA", "arguments": {}},
            {"id": "n2", "tool": "toolB", "arguments": {}},
            {"id": "n3", "tool": "toolC", "arguments": {}}
        ],
        "edges": [
            {"from_node": "n1", "to_node": "n2"},
            {"from_node": "n1", "to_node": "n3"}
        ],
        "start_node": "n1"
    }
    result = await engine.execute(config)
    assert result["status"] == "completed"
    assert result["path"][0] == "n1"
    assert result["path"][1] in ("n2", "n3")
    assert len(result["results"]) == 2

@pytest.mark.asyncio
async def test_cycle_detection():
    mcp_client = AsyncMock()
    mcp_client.call_tool = AsyncMock(return_value={"result": 1})
    engine = LangGraphEngine(mcp_client=mcp_client)
    config = {
        "nodes": [
            {"id": "n1", "tool": "toolA", "arguments": {}},
            {"id": "n2", "tool": "toolB", "arguments": {}}
        ],
        "edges": [
            {"from_node": "n1", "to_node": "n2"},
            {"from_node": "n2", "to_node": "n1"}
        ],
        "start_node": "n1"
    }
    result = await engine.execute(config)
    assert result["status"] == "failed"
    assert "n1" in result["errors"] or "n2" in result["errors"]
    assert "Cycle detected" in list(result["errors"].values())[0]

@pytest.mark.asyncio
async def test_tool_failure():
    mcp_client = AsyncMock()
    mcp_client.call_tool = AsyncMock(side_effect=[{"result": 1}, Exception("fail")])
    engine = LangGraphEngine(mcp_client=mcp_client)
    config = {
        "nodes": [
            {"id": "n1", "tool": "toolA", "arguments": {}},
            {"id": "n2", "tool": "toolB", "arguments": {}}
        ],
        "edges": [
            {"from_node": "n1", "to_node": "n2"}
        ],
        "start_node": "n1"
    }
    result = await engine.execute(config)
    assert result["status"] == "failed"
    assert "n2" in result["errors"]
    assert "fail" in result["errors"]["n2"]

@pytest.mark.asyncio
async def test_empty_workflow():
    mcp_client = AsyncMock()
    engine = LangGraphEngine(mcp_client=mcp_client)
    config = {"nodes": [], "edges": [], "start_node": "n1"}
    result = await engine.execute(config)
    assert result["status"] == "failed"
    assert result["errors"]

@pytest.mark.asyncio
async def test_missing_node():
    mcp_client = AsyncMock()
    engine = LangGraphEngine(mcp_client=mcp_client)
    config = {
        "nodes": [
            {"id": "n1", "tool": "toolA", "arguments": {}}
        ],
        "edges": [
            {"from_node": "n1", "to_node": "n2"}
        ],
        "start_node": "n1"
    }
    result = await engine.execute(config)
    assert result["status"] == "failed"
    assert "n2" in result["errors"] or "n1" in result["errors"] 