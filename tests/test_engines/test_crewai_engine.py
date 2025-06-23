import pytest
from unittest.mock import AsyncMock
from app.engines.crewai_engine import CrewAIEngine
from app.engines.schemas import CrewAIWorkflowConfig, CrewAITaskConfig

@pytest.mark.asyncio
async def test_happy_path():
    mcp_client = AsyncMock()
    mcp_client.call_tool = AsyncMock(side_effect=[{"result": 1}, {"result": 2}])
    engine = CrewAIEngine(mcp_client=mcp_client)
    config = {
        "tasks": [
            {"name": "task1", "tool": "toolA", "arguments": {}},
            {"name": "task2", "tool": "toolB", "arguments": {}, "depends_on": ["task1"]},
        ]
    }
    result = await engine.execute(config)
    assert result["status"] == "completed"
    assert set(result["results"].keys()) == {"task1", "task2"}
    assert not result["errors"]

@pytest.mark.asyncio
async def test_task_failure():
    mcp_client = AsyncMock()
    mcp_client.call_tool = AsyncMock(side_effect=[{"result": 1}, Exception("fail")])
    engine = CrewAIEngine(mcp_client=mcp_client)
    config = {
        "tasks": [
            {"name": "task1", "tool": "toolA", "arguments": {}},
            {"name": "task2", "tool": "toolB", "arguments": {}, "depends_on": ["task1"]},
        ]
    }
    result = await engine.execute(config)
    assert result["status"] == "failed"
    assert "task1" in result["results"]
    assert "task2" in result["errors"]
    assert "fail" in result["errors"]["task2"]

@pytest.mark.asyncio
async def test_missing_dependency():
    mcp_client = AsyncMock()
    mcp_client.call_tool = AsyncMock(return_value={"result": 1})
    engine = CrewAIEngine(mcp_client=mcp_client)
    config = {
        "tasks": [
            {"name": "task2", "tool": "toolB", "arguments": {}, "depends_on": ["task1"]},
        ]
    }
    result = await engine.execute(config)
    assert result["status"] == "failed"
    assert "task2" in result["errors"]
    assert "Dependencies not met" in result["errors"]["task2"]

@pytest.mark.asyncio
async def test_empty_workflow():
    mcp_client = AsyncMock()
    engine = CrewAIEngine(mcp_client=mcp_client)
    config = {"tasks": []}
    result = await engine.execute(config)
    assert result["status"] == "completed"
    assert not result["results"]
    assert not result["errors"]

@pytest.mark.asyncio
async def test_circular_dependency():
    mcp_client = AsyncMock()
    mcp_client.call_tool = AsyncMock(return_value={"result": 1})
    engine = CrewAIEngine(mcp_client=mcp_client)
    config = {
        "tasks": [
            {"name": "task1", "tool": "toolA", "arguments": {}, "depends_on": ["task2"]},
            {"name": "task2", "tool": "toolB", "arguments": {}, "depends_on": ["task1"]},
        ]
    }
    # Should not infinite loop; both tasks will be visited, but dependencies not met
    result = await engine.execute(config)
    assert result["status"] == "failed"
    assert "task1" in result["errors"] or "task2" in result["errors"] 