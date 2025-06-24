"""
from unittest.mock import AsyncMock, patch

import pytest

from app.engines.crewai_engine import CrewAIEngine
from app.engines.langgraph_engine import LangGraphEngine
from app.engines.schemas import WorkflowTask, WorkflowDefinition


@patch("crewai.llm.BaseLLM.call", return_value="dummy response")
@pytest.mark.asyncio
async def test_happy_path(mock_llm):
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

@patch("crewai.llm.BaseLLM.call", return_value="dummy response")
@pytest.mark.asyncio
async def test_task_failure(mock_llm):
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

@patch("crewai.llm.BaseLLM.call", return_value="dummy response")
@pytest.mark.asyncio
async def test_missing_dependency(mock_llm):
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

@patch("crewai.llm.BaseLLM.call", return_value="dummy response")
@pytest.mark.asyncio
async def test_empty_workflow(mock_llm):
    mcp_client = AsyncMock()
    engine = CrewAIEngine(mcp_client=mcp_client)
    config = {"tasks": []}
    result = await engine.execute(config)
    assert result["status"] == "completed"
    assert not result["results"]
    assert not result["errors"]

@patch("crewai.llm.BaseLLM.call", return_value="dummy response")
@pytest.mark.asyncio
async def test_circular_dependency(mock_llm):
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

@pytest.mark.asyncio
def test_workflow_parity_between_engines():
    mcp_client = AsyncMock()
    mcp_client.call_tool = AsyncMock(side_effect=[{"result": 1}, {"result": 2}])
    # Canonical workflow definition
    workflow = WorkflowDefinition(
        workflow_id="parity-test-1",
        tasks=[
            WorkflowTask(id="task1", tool="toolA", arguments={}, depends_on=[]),
            WorkflowTask(id="task2", tool="toolB", arguments={}, depends_on=["task1"]),
        ]
    )
    crew_engine = CrewAIEngine(mcp_client=mcp_client)
    lang_engine = LangGraphEngine(mcp_client=mcp_client)
    crew_result = pytest.run(asyncio=True)(crew_engine.execute_workflow)(workflow)
    lang_result = pytest.run(asyncio=True)(lang_engine.execute_workflow)(workflow)
    # Compare status, results, and errors
    assert crew_result["status"] == lang_result["status"]
    assert crew_result["results"] == lang_result["results"]
    assert crew_result["errors"] == lang_result["errors"]

"""
