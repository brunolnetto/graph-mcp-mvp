from unittest.mock import AsyncMock

import pytest

from app.engines.langgraph_engine import LangGraphEngine


@pytest.mark.asyncio
async def test_happy_path():
    mcp_client = AsyncMock()
    mcp_client.call_tool = AsyncMock(side_effect=[{"result": 1}, {"result": 2}])
    engine = LangGraphEngine(mcp_client=mcp_client)
    config = {
        "nodes": [
            {"id": "n1", "tool": "toolA", "arguments": {}},
            {"id": "n2", "tool": "toolB", "arguments": {}},
        ],
        "edges": [{"from_node": "n1", "to_node": "n2"}],
        "start_node": "n1",
    }
    result = await engine.execute(config)
    print("HAPPY PATH RESULT:", result)
    assert result["status"] == "completed"
    assert result["path"] == ["n1", "n2"]
    assert set(result["results"].keys()) == {"n1", "n2"}
    assert not result["errors"]


@pytest.mark.asyncio
async def test_branching_success():
    mcp_client = AsyncMock()
    mcp_client.call_tool = AsyncMock(
        side_effect=[{"result": 1}, {"result": 2}, {"result": 3}]
    )
    engine = LangGraphEngine(mcp_client=mcp_client)
    config = {
        "nodes": [
            {"id": "n1", "tool": "toolA", "arguments": {}},
            {"id": "n2", "tool": "toolB", "arguments": {}},
            {"id": "n3", "tool": "toolC", "arguments": {}},
        ],
        "edges": [
            {"from_node": "n1", "to_node": "n2"},
            {"from_node": "n1", "to_node": "n3"},
        ],
        "start_node": "n1",
    }
    result = await engine.execute(config)
    print("BRANCHING SUCCESS RESULT:", result)
    assert result["status"] == "completed"
    assert set(result["results"].keys()) == {"n1", "n2", "n3"}
    assert not result["errors"]


@pytest.mark.asyncio
async def test_branching_with_error():
    mcp_client = AsyncMock()
    mcp_client.call_tool = AsyncMock(
        side_effect=[{"result": 1}, {"result": 2}]
    )  # n2 or n3 will error
    engine = LangGraphEngine(mcp_client=mcp_client)
    config = {
        "nodes": [
            {"id": "n1", "tool": "toolA", "arguments": {}},
            {"id": "n2", "tool": "toolB", "arguments": {}},
            {"id": "n3", "tool": "toolC", "arguments": {}},
        ],
        "edges": [
            {"from_node": "n1", "to_node": "n2"},
            {"from_node": "n1", "to_node": "n3"},
        ],
        "start_node": "n1",
    }
    result = await engine.execute(config)
    print("BRANCHING ERROR RESULT:", result)
    assert result["status"] == "failed"
    error_keys = set(result["errors"].keys())
    assert error_keys in [{"n2"}, {"n3"}]
    result_keys = set(result["results"].keys())
    assert result_keys in [{"n1", "n2"}, {"n1", "n3"}]


@pytest.mark.asyncio
async def test_cycle_detection():
    mcp_client = AsyncMock()
    mcp_client.call_tool = AsyncMock(return_value={"result": 1})
    engine = LangGraphEngine(mcp_client=mcp_client)
    config = {
        "nodes": [
            {"id": "n1", "tool": "toolA", "arguments": {}},
            {"id": "n2", "tool": "toolB", "arguments": {}},
        ],
        "edges": [
            {"from_node": "n1", "to_node": "n2"},
            {"from_node": "n2", "to_node": "n1"},
        ],
        "start_node": "n1",
    }
    result = await engine.execute(config)
    assert result["status"] == "failed"
    assert "error" in result["errors"]
    assert "Recursion limit" in result["errors"]["error"]


@pytest.mark.asyncio
async def test_tool_failure():
    mcp_client = AsyncMock()
    mcp_client.call_tool = AsyncMock(side_effect=[{"result": 1}, Exception("fail")])
    engine = LangGraphEngine(mcp_client=mcp_client)
    config = {
        "nodes": [
            {"id": "n1", "tool": "toolA", "arguments": {}},
            {"id": "n2", "tool": "toolB", "arguments": {}},
        ],
        "edges": [{"from_node": "n1", "to_node": "n2"}],
        "start_node": "n1",
    }
    result = await engine.execute(config)
    assert result["status"] == "failed"
    assert "error" in result["errors"] or "n2" in result["errors"]


@pytest.mark.asyncio
async def test_empty_workflow():
    mcp_client = AsyncMock()
    engine = LangGraphEngine(mcp_client=mcp_client)
    config = {"nodes": [], "edges": [], "start_node": "n1"}
    result = await engine.execute(config)
    assert result["status"] == "failed"
    assert "error" in result["errors"]
    assert (
        "entrypoint" in result["errors"]["error"]
        or "edge ending" in result["errors"]["error"]
    )


@pytest.mark.asyncio
async def test_missing_node():
    mcp_client = AsyncMock()
    engine = LangGraphEngine(mcp_client=mcp_client)
    config = {
        "nodes": [{"id": "n1", "tool": "toolA", "arguments": {}}],
        "edges": [{"from_node": "n1", "to_node": "n2"}],
        "start_node": "n1",
    }
    result = await engine.execute(config)
    assert result["status"] == "failed"
    assert "error" in result["errors"]
    assert (
        "edge ending" in result["errors"]["error"]
        or "unknown target" in result["errors"]["error"]
    )


@pytest.mark.asyncio
async def test_execute_workflow_not_implemented():
    engine = LangGraphEngine()
    with pytest.raises(NotImplementedError):
        await engine.execute_workflow({})


@pytest.mark.asyncio
async def test_get_workflow_status_not_implemented():
    engine = LangGraphEngine()
    with pytest.raises(NotImplementedError):
        await engine.get_workflow_status("workflow_id")


@pytest.mark.asyncio
async def test_cancel_workflow_not_implemented():
    engine = LangGraphEngine()
    with pytest.raises(NotImplementedError):
        await engine.cancel_workflow("workflow_id")


@pytest.mark.asyncio
async def test_missing_mcp_client():
    engine = LangGraphEngine(mcp_client=None)
    config = {
        "nodes": [{"id": "n1", "tool": "toolA", "arguments": {}}],
        "edges": [],
        "start_node": "n1",
    }
    result = await engine.execute(config)
    assert result["status"] == "failed"
    assert "n1" in result["errors"]
    assert "MCPClient not provided" in result["errors"]["n1"]


@pytest.mark.asyncio
async def test_edge_condition_eval_error():
    mcp_client = AsyncMock()
    mcp_client.call_tool = AsyncMock(return_value={"result": 1})
    engine = LangGraphEngine(mcp_client=mcp_client)
    config = {
        "nodes": [{"id": "n1", "tool": "toolA", "arguments": {}}],
        "edges": [
            {
                "from_node": "n1",
                "to_node": "n2",
                "condition": "raise Exception('bad cond')",
            }
        ],
        "start_node": "n1",
    }
    result = await engine.execute(config)
    assert result["status"] == "failed"
    assert "error" in result["errors"]
    assert (
        "unknown target" in result["errors"]["error"]
        or "At 'n1' node" in result["errors"]["error"]
    )
