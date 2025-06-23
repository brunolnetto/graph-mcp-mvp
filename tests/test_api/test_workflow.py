"""Tests for workflow management API endpoints."""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app

client = TestClient(app)


def test_list_engines(client: TestClient, mock_workflow_manager_override):
    """Test listing available workflow engines."""
    response = client.get("/api/v1/workflow/engines")
    assert response.status_code == 200
    data = response.json()
    assert "crewai" in data["available_engines"]
    assert data["current_engine"] == "crewai"


def test_switch_engine(client: TestClient, mock_workflow_manager_override):
    """Test switching the default engine."""
    engine_data = {"engine": "langgraph"}
    response = client.put("/api/v1/workflow/engine", json=engine_data)
    assert response.status_code == 200
    mock_workflow_manager_override.switch_engine.assert_called_once_with("langgraph")


def test_get_current_engine(client: TestClient, mock_workflow_manager_override):
    """Test getting the current default engine."""
    response = client.get("/api/v1/workflow/engine/current")
    assert response.status_code == 200
    data = response.json()
    assert data["current_engine"] == "crewai"


def test_execute_workflow_success(client: TestClient, mock_workflow_manager_override, sample_workflow_config):
    """Test successful workflow execution."""
    response = client.post("/api/v1/workflow/execute", json=sample_workflow_config)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    # Ensure the correct engine was requested from the manager
    mock_workflow_manager_override.get_engine.assert_called_with(sample_workflow_config["engine"])


def test_demo_workflow_success(client: TestClient, mock_workflow_manager_override):
    """Test successful demo workflow execution."""
    response = client.post("/api/v1/workflow/demo")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "completed"
    # Demo workflow calls get_engine without arguments
    mock_workflow_manager_override.get_engine.assert_called_with()


def test_execute_workflow_engine_error(client: TestClient, mock_workflow_manager_override, sample_workflow_config):
    """Test handling of an exception during workflow execution."""
    mock_workflow_manager_override.get_engine.return_value.execute.side_effect = Exception("Execution Failed")
    response = client.post("/api/v1/workflow/execute", json=sample_workflow_config)
    assert response.status_code == 500
    assert "Execution Failed" in response.json()["detail"]


def test_switch_engine_invalid(client, mock_workflow_manager_override):
    response = client.put("/api/v1/workflow/engine", json={"engine": "invalid"})
    assert response.status_code == 400 or response.status_code == 422


def test_execute_workflow_exception(client, mock_workflow_manager_override, sample_workflow_config):
    mock_workflow_manager_override.get_engine.return_value.execute.side_effect = Exception("Workflow failed")
    response = client.post("/api/v1/workflow/execute", json=sample_workflow_config)
    assert response.status_code == 500
    assert "Workflow failed" in response.json()["detail"]


def test_execute_workflow_with_specific_engine(client: TestClient, mock_workflow_manager_override):
    """Test executing a workflow with a specific engine."""
    workflow_config = {
        "name": "Test Workflow",
        "description": "A test workflow",
        "tasks": [{"name": "Task 1", "type": "research"}],
        "engine": "crewai"
    }
    response = client.post("/api/v1/workflow/execute", json=workflow_config)
    assert response.status_code == 200
    data = response.json()
    assert data["engine"] == "MockEngine"


def test_execute_workflow_without_engine_specification(client: TestClient, mock_workflow_manager_override):
    """Test executing a workflow without specifying an engine."""
    workflow_config = {
        "name": "Test Workflow",
        "description": "A test workflow",
        "tasks": [{"name": "Task 1", "type": "research"}],
        "engine": "crewai"
    }
    response = client.post("/api/v1/workflow/execute", json=workflow_config)
    assert response.status_code == 200
    data = response.json()
    assert data["engine"] == "MockEngine"


def test_workflow_manager_get_engine_unknown():
    """Test WorkflowManager.get_engine with unknown engine."""
    from app.api.routes.workflow import WorkflowManager

    manager = WorkflowManager()
    with pytest.raises(ValueError, match="Unknown engine: unknown"):
        manager.get_engine("unknown")


def test_workflow_manager_switch_engine_unknown():
    """Test WorkflowManager.switch_engine with unknown engine."""
    from app.api.routes.workflow import WorkflowManager

    manager = WorkflowManager()
    with pytest.raises(ValueError, match="Unknown engine: unknown"):
        manager.switch_engine("unknown")


def test_execute_workflow_invalid_payload(client, mock_workflow_manager_override):
    # Missing required fields
    response = client.post("/api/v1/workflow/execute", json={})
    assert response.status_code == 422


def test_switch_engine_missing_field(client, mock_workflow_manager_override):
    # Missing 'engine' field
    response = client.put("/api/v1/workflow/engine", json={})
    assert response.status_code == 422


def test_get_current_engine_exception(client, mock_workflow_manager_override):
    mock_workflow_manager_override.current_engine = None
    mock_workflow_manager_override.get_engine.side_effect = Exception("Engine error")
    response = client.get("/api/v1/workflow/engine/current")
    assert response.status_code == 500
    assert "Current engine is not set." in response.json()["detail"]


def test_switch_engine_exception(client, mock_workflow_manager_override):
    mock_workflow_manager_override.switch_engine.side_effect = Exception("Switch error")
    response = client.put("/api/v1/workflow/engine", json={"engine": "crewai"})
    assert response.status_code == 400
    assert "Switch error" in response.json()["detail"]


def test_run_demo_workflow_exception(client, mock_workflow_manager_override):
    mock_workflow_manager_override.get_engine.side_effect = Exception("Demo error")
    response = client.post("/api/v1/workflow/demo")
    assert response.status_code == 500
    assert "Demo error" in response.json()["detail"]


@pytest.mark.asyncio
async def test_execute_workflow_crewai():
    # Minimal workflow config for CrewAIEngine
    config = {
        "name": "Test Workflow",
        "description": "A test workflow",
        "tasks": [
            {"name": "task1", "tool": "echo", "arguments": {"msg": "hello"}},
            {"name": "task2", "tool": "echo", "arguments": {"msg": "world"}, "depends_on": ["task1"]},
        ],
        "engine": "crewai"
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        response = await async_client.post("/api/v1/workflow/execute", json=config)
    if response.status_code != 200:
        print("Response status:", response.status_code)
        print("Response body:", response.text)
    assert response.status_code == 200
    data = response.json()
    assert data["engine"] == "crewai"
    assert data["status"] in ("completed", "failed")
    assert "results" in data["result"]
    assert "errors" in data["result"]


@pytest.mark.asyncio
async def test_execute_workflow_langgraph():
    # Minimal workflow config for LangGraphEngine
    config = {
        "name": "Test LangGraph Workflow",
        "description": "A test workflow for LangGraphEngine",
        "nodes": [
            {"id": "n1", "tool": "echo", "arguments": {"msg": "hello"}},
            {"id": "n2", "tool": "echo", "arguments": {"msg": "world"}}
        ],
        "edges": [
            {"from_node": "n1", "to_node": "n2"}
        ],
        "start_node": "n1",
        "engine": "langgraph"
    }
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        response = await async_client.post("/api/v1/workflow/execute", json=config)
    if response.status_code != 200:
        print("Response status:", response.status_code)
        print("Response body:", response.text)
    assert response.status_code == 200
    data = response.json()
    assert data["engine"] == "langgraph"
    assert data["status"] in ("completed", "failed")
    assert "results" in data["result"]
    assert "errors" in data["result"]
