"""Tests for workflow management API endpoints."""

import pytest
from fastapi.testclient import TestClient

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


def test_switch_engine_invalid(client: TestClient):
    """Test switching to an invalid engine. This should be caught by Pydantic."""
    engine_switch_data = {"engine": "invalid_engine"}
    response = client.put("/api/v1/workflow/engine", json=engine_switch_data)
    assert response.status_code == 422 # Pydantic validation error


def test_execute_workflow_with_specific_engine(client: TestClient, mock_workflow_manager_override):
    """Test executing a workflow with a specific engine."""
    workflow_config = {
        "name": "Test Workflow",
        "description": "A test workflow",
        "tasks": [{"name": "Task 1", "type": "research"}],
        "engine": "langgraph"
    }
    response = client.post("/api/v1/workflow/execute", json=workflow_config)
    assert response.status_code == 200
    data = response.json()
    assert data["engine"] == "Langgraph"


def test_execute_workflow_without_engine_specification(client: TestClient, mock_workflow_manager_override):
    """Test executing a workflow without specifying an engine."""
    workflow_config = {
        "name": "Test Workflow",
        "description": "A test workflow",
        "tasks": [{"name": "Task 1", "type": "research"}]
    }
    response = client.post("/api/v1/workflow/execute", json=workflow_config)
    assert response.status_code == 200
    data = response.json()
    assert data["engine"] == "Crewai"


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