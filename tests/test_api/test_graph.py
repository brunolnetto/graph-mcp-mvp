"""Tests for graph operations API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from app.main import app

client = TestClient(app)


def test_create_node(client: TestClient, mock_neo4j_override, sample_node_data):
    """Test creating a node."""
    mock_neo4j_override.create_node.return_value = {
        "id": 123,
        **sample_node_data,
    }
    response = client.post("/api/v1/graph/nodes", json=sample_node_data)
    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["labels"] == sample_node_data["labels"]
    assert data["properties"] == sample_node_data["properties"]
    mock_neo4j_override.create_node.assert_called_once_with(
        sample_node_data["labels"], sample_node_data["properties"]
    )


def test_get_nodes(client: TestClient, mock_neo4j_override):
    """Test getting nodes."""
    mock_neo4j_override.get_nodes.return_value = []
    response = client.get("/api/v1/graph/nodes")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_nodes_with_labels(client: TestClient, mock_neo4j_override):
    """Test getting nodes with specific labels."""
    mock_neo4j_override.get_nodes.return_value = []
    response = client.get("/api/v1/graph/nodes?labels=Person")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    mock_neo4j_override.get_nodes.assert_called_once()


def test_execute_cypher_query(client: TestClient, mock_neo4j_override):
    """Test executing a Cypher query."""
    mock_neo4j_override.execute_cypher.return_value = [{"result": "success"}]
    query_data = {"query": "MATCH (n) RETURN n LIMIT 10", "parameters": {}}
    response = client.post("/api/v1/graph/query", json=query_data)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data


def test_get_graph_stats_success(client: TestClient, mock_neo4j_override):
    """Test getting graph stats successfully."""
    mock_neo4j_override.get_graph_stats.return_value = {
        "total_nodes": 10,
        "total_relationships": 5,
    }
    response = client.get("/api/v1/graph/stats")
    assert response.status_code == 200
    assert response.json()["total_nodes"] == 10


def test_get_graph_stats_error(client: TestClient, mock_neo4j_override):
    """Test error handling when getting graph stats."""
    mock_neo4j_override.get_graph_stats.side_effect = Exception("DB error")
    response = client.get("/api/v1/graph/stats")
    assert response.status_code == 500
    assert "DB error" in response.json()["detail"]


def test_create_node_invalid_data(client: TestClient):
    """Test creating a node with invalid data."""
    invalid_data = {"labels": ["Test"], "properties": "not a dict"}
    response = client.post("/api/v1/graph/nodes", json=invalid_data)
    assert response.status_code == 422


def test_execute_cypher_invalid_query(client: TestClient):
    """Test executing an invalid Cypher query."""
    query_data = {"query": "", "parameters": {}}
    response = client.post("/api/v1/graph/query", json=query_data)
    assert response.status_code == 422


def test_create_node_exception(client: TestClient, mock_neo4j_override, sample_node_data):
    """Test creating a node when an exception occurs."""
    mock_neo4j_override.create_node.side_effect = Exception("Database error")
    response = client.post("/api/v1/graph/nodes", json=sample_node_data)
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"]


def test_get_nodes_exception(client: TestClient, mock_neo4j_override):
    """Test getting nodes when an exception occurs."""
    mock_neo4j_override.get_nodes.side_effect = Exception("Database error")
    response = client.get("/api/v1/graph/nodes?labels=Person")
    assert response.status_code == 500
    assert "Database error" in response.json()["detail"]


def test_execute_cypher_exception(client: TestClient, mock_neo4j_override):
    """Test executing Cypher query when an exception occurs."""
    mock_neo4j_override.execute_cypher.side_effect = Exception("Query error")
    query_data = {"query": "MATCH (n) RETURN n", "parameters": {}}
    response = client.post("/api/v1/graph/query", json=query_data)
    assert response.status_code == 500
    assert "Query error" in response.json()["detail"]


def test_get_graph_stats_exception(client: TestClient, mock_neo4j_override):
    """Test getting graph stats when an exception occurs."""
    mock_neo4j_override.get_graph_stats.side_effect = Exception("Stats error")
    response = client.get("/api/v1/graph/stats")
    assert response.status_code == 500
    assert "Stats error" in response.json()["detail"]


def test_get_nodes_with_comma_separated_labels(client: TestClient, mock_neo4j_override):
    """Test getting nodes with comma-separated labels."""
    mock_neo4j_override.get_nodes.return_value = []
    response = client.get("/api/v1/graph/nodes?labels=Person,User")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    mock_neo4j_override.get_nodes.assert_called_once()
    call_args, call_kwargs = mock_neo4j_override.get_nodes.call_args
    assert call_args[0] == ['Person', 'User']
    assert call_args[1] is None  # properties
    assert call_args[2] == 100  # limit


def test_get_nodes_success(client: TestClient, mock_neo4j_override):
    """Test getting nodes successfully."""
    mock_neo4j_override.get_nodes.return_value = [
        {"id": 1, "labels": ["Test"], "properties": {"name": "test_node"}}
    ]
    response = client.get("/api/v1/graph/nodes?labels=Test")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["properties"]["name"] == "test_node"


def test_create_node_success(client: TestClient, mock_neo4j_override):
    """Test creating a node successfully."""
    mock_neo4j_override.create_node.return_value = {
        "id": 1,
        "labels": ["Test"],
        "properties": {"name": "test_node"},
    }
    response = client.post(
        "/api/v1/graph/nodes",
        json={"labels": ["Test"], "properties": {"name": "test_node"}},
    )
    assert response.status_code == 201
    assert response.json()["properties"]["name"] == "test_node" 