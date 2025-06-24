"""Tests for graph operations API endpoints."""

from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_neo4j_client
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


@pytest.mark.asyncio
async def test_execute_cypher_query():
    """Test executing a Cypher query."""

    class FakeNeo4jClient:
        async def execute_query(self, *args, **kwargs):
            return [{"result": "success"}]

    app.dependency_overrides[get_neo4j_client] = lambda: FakeNeo4jClient()
    query_data = {"query": "MATCH (n) RETURN n LIMIT 10", "parameters": {}}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        response = await async_client.post("/api/v1/graph/query", json=query_data)
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    app.dependency_overrides.clear()


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


def test_create_node_exception(
    client: TestClient, mock_neo4j_override, sample_node_data
):
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


@pytest.mark.asyncio
async def test_execute_cypher_exception():
    """Test executing Cypher query when an exception occurs."""

    class FakeNeo4jClient:
        async def execute_query(self, *args, **kwargs):
            raise Exception("Query error")

    app.dependency_overrides[get_neo4j_client] = lambda: FakeNeo4jClient()
    query_data = {"query": "MATCH (n) RETURN n", "parameters": {}}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as async_client:
        response = await async_client.post("/api/v1/graph/query", json=query_data)
    assert response.status_code == 500
    assert "Query error" in response.json()["detail"]
    app.dependency_overrides.clear()


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
    assert call_args[0] == ["Person", "User"]
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


def test_delete_node_not_found(client, mock_neo4j_override):
    mock_neo4j_override.delete_node = AsyncMock(return_value=False)
    response = client.delete("/api/v1/graph/nodes/999")
    print("RESPONSE:", response.status_code, response.text)
    assert response.status_code == 404
    assert response.json()["detail"] == "Node not found"


def test_delete_node_value_error(client, mock_neo4j_override):
    mock_neo4j_override.delete_node.side_effect = ValueError("Custom not found")
    response = client.delete("/api/v1/graph/nodes/123")
    assert response.status_code == 404
    assert "Custom not found" in response.json()["detail"]


def test_delete_node_exception(client, mock_neo4j_override):
    mock_neo4j_override.delete_node.side_effect = Exception("DB error")
    response = client.delete("/api/v1/graph/nodes/1")
    assert response.status_code == 500
    assert "DB error" in response.json()["detail"]


def test_create_relationship_not_found(client, mock_neo4j_override):
    mock_neo4j_override.create_relationship.return_value = None
    response = client.post(
        "/api/v1/graph/relationships",
        params={"from_node_id": 1, "to_node_id": 2, "relationship_type": "KNOWS"},
        json={},
    )
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_relationship_exception(client, mock_neo4j_override):
    mock_neo4j_override.create_relationship.side_effect = Exception(
        "Relationship error"
    )
    response = client.post(
        "/api/v1/graph/relationships",
        params={"from_node_id": 1, "to_node_id": 2, "relationship_type": "KNOWS"},
        json={},
    )
    assert response.status_code == 500
    assert "Relationship error" in response.json()["detail"]


def test_update_node_not_found(client, mock_neo4j_override):
    mock_neo4j_override.update_node.side_effect = ValueError("Node not found")
    response = client.put("/api/v1/graph/nodes/123", json={"name": "new"})
    assert response.status_code == 404
    assert "Node not found" in response.json()["detail"]


def test_update_node_exception(client, mock_neo4j_override):
    mock_neo4j_override.update_node.side_effect = Exception("Update error")
    response = client.put("/api/v1/graph/nodes/123", json={"name": "new"})
    assert response.status_code == 500
    assert "Update error" in response.json()["detail"]


def test_update_node_value_error_explicit(client, mock_neo4j_override):
    mock_neo4j_override.update_node.side_effect = ValueError("Explicit value error")
    response = client.put("/api/v1/graph/nodes/999", json={"foo": "bar"})
    assert response.status_code == 404
    assert "Explicit value error" in response.json()["detail"]


def test_update_node_generic_exception_explicit(client, mock_neo4j_override):
    mock_neo4j_override.update_node.side_effect = Exception("Explicit generic error")
    response = client.put("/api/v1/graph/nodes/999", json={"foo": "bar"})
    assert response.status_code == 500
    assert "Explicit generic error" in response.json()["detail"]


def test_delete_node_generic_exception_explicit(client, mock_neo4j_override):
    mock_neo4j_override.delete_node.side_effect = Exception("Explicit delete error")
    response = client.delete("/api/v1/graph/nodes/999")
    assert response.status_code == 500
    assert "Explicit delete error" in response.json()["detail"]


def test_get_graph_stats_generic_exception_explicit(client, mock_neo4j_override):
    mock_neo4j_override.get_graph_stats.side_effect = Exception("Explicit stats error")
    response = client.get("/api/v1/graph/stats")
    assert response.status_code == 500
    assert "Explicit stats error" in response.json()["detail"]


def test_update_node_value_error_granular(client, mock_neo4j_override):
    mock_neo4j_override.update_node.side_effect = ValueError("Granular value error")
    response = client.put("/api/v1/graph/nodes/111", json={"foo": "bar"})
    assert response.status_code == 404
    assert "Granular value error" in response.json()["detail"]


def test_update_node_exception_granular(client, mock_neo4j_override):
    mock_neo4j_override.update_node.side_effect = Exception("Granular generic error")
    response = client.put("/api/v1/graph/nodes/112", json={"foo": "bar"})
    assert response.status_code == 500
    assert "Granular generic error" in response.json()["detail"]


def test_delete_node_exception_granular(client, mock_neo4j_override):
    mock_neo4j_override.delete_node.side_effect = Exception("Granular delete error")
    response = client.delete("/api/v1/graph/nodes/113")
    assert response.status_code == 500
    assert "Granular delete error" in response.json()["detail"]


def test_get_graph_stats_exception_granular(client, mock_neo4j_override):
    mock_neo4j_override.get_graph_stats.side_effect = Exception("Granular stats error")
    response = client.get("/api/v1/graph/stats")
    assert response.status_code == 500
    assert "Granular stats error" in response.json()["detail"]


def test_update_node_value_error_100(client, mock_neo4j_override):
    mock_neo4j_override.update_node.side_effect = ValueError("100% ValueError")
    response = client.put("/api/v1/graph/nodes/201", json={"foo": "bar"})
    assert response.status_code == 404
    assert "100% ValueError" in response.json()["detail"]


def test_update_node_exception_100(client, mock_neo4j_override):
    mock_neo4j_override.update_node.side_effect = Exception("100% Exception")
    response = client.put("/api/v1/graph/nodes/202", json={"foo": "bar"})
    assert response.status_code == 500
    assert "100% Exception" in response.json()["detail"]


def test_delete_node_exception_100(client, mock_neo4j_override):
    mock_neo4j_override.delete_node.side_effect = Exception("100% Delete Exception")
    response = client.delete("/api/v1/graph/nodes/203")
    assert response.status_code == 500
    assert "100% Delete Exception" in response.json()["detail"]


def test_create_relationship_exception_100(client, mock_neo4j_override):
    mock_neo4j_override.create_relationship.side_effect = Exception(
        "100% Relationship Exception"
    )
    response = client.post(
        "/api/v1/graph/relationships",
        params={"from_node_id": 1, "to_node_id": 2, "relationship_type": "KNOWS"},
        json={},
    )
    assert response.status_code == 500
    assert "100% Relationship Exception" in response.json()["detail"]


def test_shortest_path(client, mock_neo4j_client):
    mock_neo4j_client.shortest_path.return_value = [1, 2, 3]
    resp = client.post(
        "/api/v1/graph/shortest-path", json={"source_id": 1, "target_id": 3}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "path" in data
    assert data["path"] == [1, 2, 3]


def test_shortest_path_no_path(client, mock_neo4j_client):
    mock_neo4j_client.shortest_path.return_value = []
    resp = client.post(
        "/api/v1/graph/shortest-path", json={"source_id": 10, "target_id": 20}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["path"] == []


def test_shortest_path_invalid_nodes(client, mock_neo4j_client):
    mock_neo4j_client.shortest_path.return_value = []
    resp = client.post(
        "/api/v1/graph/shortest-path", json={"source_id": 999, "target_id": 888}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["path"] == []
