"""Pytest configuration and fixtures."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.dependencies import get_neo4j_client, get_workflow_manager
from app.main import app


@pytest.fixture
def client():
    """Test client for FastAPI application."""
    return TestClient(app)


@pytest.fixture
def mock_neo4j_override():
    """Override the Neo4j client dependency with a mock."""
    mock_client = AsyncMock()
    app.dependency_overrides[get_neo4j_client] = lambda: mock_client
    yield mock_client
    app.dependency_overrides.clear()


@pytest.fixture
def mock_workflow_manager_override():
    """Override the WorkflowManager dependency with a mock."""
    mock_manager = MagicMock()

    # This engine will be returned by the manager.
    # Its `execute` method must be awaitable, so it's an AsyncMock.
    mock_engine = AsyncMock()
    mock_engine.name = "MockEngine"

    # The result when the endpoint calls `await engine.execute(...)`
    mock_engine.execute.return_value = {
        "workflow_id": "mock_workflow_123",
        "status": "completed",
        "result": {"message": "Mock execution successful"},
        "engine": "MockEngine",
    }

    # Configure the manager to return our mock engine
    mock_manager.get_engine.return_value = mock_engine
    mock_manager.current_engine = "crewai"

    app.dependency_overrides[get_workflow_manager] = lambda: mock_manager
    yield mock_manager
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def mock_neo4j_client():
    mock = AsyncMock()
    mock.shortest_path.return_value = [1, 2, 3]
    app.dependency_overrides[get_neo4j_client] = lambda: mock
    yield mock
    app.dependency_overrides = {}


@pytest.fixture
def mock_workflow_manager():
    """Mock workflow manager for testing."""
    mock_manager = MagicMock()
    mock_manager.current_engine = "crewai"
    mock_manager.get_engine.return_value = AsyncMock()
    return mock_manager


@pytest.fixture
def sample_node_data():
    """Sample node data for testing."""
    return {"labels": ["Person"], "properties": {"name": "John Doe", "age": 30}}


@pytest.fixture
def sample_workflow_config():
    """Sample workflow configuration for testing (canonical schema)."""
    return {
        "workflow_id": "test-workflow-1",
        "tasks": [
            {"id": "task1", "tool": "toolA", "arguments": {}, "depends_on": []},
            {"id": "task2", "tool": "toolB", "arguments": {}, "depends_on": ["task1"]},
        ],
    }


@pytest.fixture(autouse=True)
def mock_litellm_completion():
    mock_message = MagicMock()
    mock_message.content = "mocked response"
    mock_choice = MagicMock()
    mock_choice.message = mock_message
    mock_response = MagicMock()
    mock_response.choices = [mock_choice]
    with patch("litellm.completion", return_value=mock_response):
        yield
