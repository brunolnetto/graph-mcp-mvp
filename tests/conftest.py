"""Pytest configuration and fixtures."""

from unittest.mock import AsyncMock, MagicMock

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


@pytest.fixture
def mock_neo4j_client():
    """Mock Neo4j client for testing."""
    mock_client = AsyncMock()
    mock_client.create_node.return_value = {
        "id": 1,
        "labels": ["Person"],
        "properties": {"name": "John Doe", "age": 30}
    }
    mock_client.get_nodes.return_value = [
        {
            "id": 1,
            "labels": ["Person"],
            "properties": {"name": "John Doe", "age": 30}
        }
    ]
    mock_client.execute_cypher.return_value = [{"result": "success"}]
    return mock_client


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
    return {
        "labels": ["Person"],
        "properties": {"name": "John Doe", "age": 30}
    }


@pytest.fixture
def sample_workflow_config():
    """Sample workflow configuration for testing."""
    return {
        "name": "Test Workflow",
        "description": "A test workflow",
        "tasks": [
            {"name": "Task 1", "type": "research"},
            {"name": "Task 2", "type": "processing"}
        ],
        "engine": "crewai"
    }
