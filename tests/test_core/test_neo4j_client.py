"""Tests for Neo4j client functionality."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from neo4j.exceptions import ClientError, ServiceUnavailable

from app.core.neo4j_client import Neo4jClient
from app.dependencies import WorkflowManager
from app.engines.crewai_engine import CrewAIEngine
from app.engines.langgraph_engine import LangGraphEngine


def create_mock_node(node_id, labels, properties):
    """Create a MagicMock that behaves like a neo4j.Node."""
    mock_node = MagicMock()
    mock_node.id = node_id
    mock_node.labels = set(labels)

    # Make the mock node behave like a dictionary for properties
    mock_node.items.return_value = properties.items()
    mock_node.keys.return_value = properties.keys()
    mock_node.values.return_value = properties.values()
    mock_node.__iter__ = lambda s: iter(properties)
    mock_node.__getitem__.side_effect = properties.__getitem__

    return mock_node


@pytest.fixture
def neo4j_client():
    """Create a clean Neo4j client instance for each test."""
    client = Neo4jClient(
        uri="bolt://localhost:7687", user="neo4j", password="password", database="neo4j"
    )
    client._driver = None  # Ensure clean state
    return client


class TestNeo4jClientConnect:
    """Tests for connection and context management."""

    @pytest.mark.asyncio
    async def test_connect_success(self, neo4j_client):
        """Test successful connection."""
        with patch("neo4j.AsyncGraphDatabase.driver") as mock_driver_class:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity = AsyncMock()
            mock_driver_class.return_value = mock_driver

            await neo4j_client.connect()

            assert neo4j_client._driver is mock_driver
            mock_driver.verify_connectivity.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure(self, neo4j_client):
        """Test connection failure."""
        with patch("neo4j.AsyncGraphDatabase.driver") as mock_driver_class:
            mock_driver = AsyncMock()
            mock_driver.verify_connectivity.side_effect = ServiceUnavailable("Failed")
            mock_driver_class.return_value = mock_driver

            with pytest.raises(ServiceUnavailable):
                await neo4j_client.connect()

    @pytest.mark.asyncio
    async def test_close(self, neo4j_client):
        """Test closing the connection."""
        mock_driver = AsyncMock()
        neo4j_client._driver = mock_driver
        await neo4j_client.close()
        mock_driver.close.assert_called_once()
        assert neo4j_client._driver is None

    @pytest.mark.asyncio
    async def test_context_manager(self, neo4j_client):
        """Test client as an async context manager."""
        with (
            patch.object(neo4j_client, "connect", new=AsyncMock()) as mock_connect,
            patch.object(neo4j_client, "close", new=AsyncMock()) as mock_close,
        ):
            async with neo4j_client:
                mock_connect.assert_called_once()
            mock_close.assert_called_once()


class TestNeo4jClientQueries:
    """Tests for query execution and CRUD operations."""

    @pytest.mark.asyncio
    async def test_execute_query_success(self, neo4j_client):
        """Test successful query execution."""
        mock_driver = AsyncMock()
        mock_session_cm = AsyncMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()

        mock_result.data.return_value = [{"name": "test"}]
        mock_session.run.return_value = mock_result
        mock_session_cm.__aenter__.return_value = mock_session
        mock_driver.session = MagicMock(return_value=mock_session_cm)
        neo4j_client._driver = mock_driver

        result = await neo4j_client.execute_query("MATCH (n) RETURN n")
        assert result == [{"name": "test"}]

    @pytest.mark.asyncio
    async def test_execute_query_failure(self, neo4j_client):
        """Test query execution failure."""
        mock_driver = AsyncMock()
        mock_session_cm = AsyncMock()
        mock_session = AsyncMock()
        mock_session.run.side_effect = ClientError("Query failed")

        mock_session_cm.__aenter__.return_value = mock_session
        mock_driver.session = MagicMock(return_value=mock_session_cm)
        neo4j_client._driver = mock_driver

        with pytest.raises(ClientError):
            await neo4j_client.execute_query("INVALID QUERY")

    @pytest.mark.asyncio
    async def test_auto_connect_on_query(self, neo4j_client):
        """Test client auto-connects before running a query."""
        with patch.object(neo4j_client, "connect", new=AsyncMock()) as mock_connect:
            # Mock the driver and session to prevent executing a real query
            async def set_driver():
                mock_driver = AsyncMock()
                mock_session_cm = AsyncMock()
                mock_session = AsyncMock()
                mock_session.run.return_value = AsyncMock()
                mock_session_cm.__aenter__.return_value = mock_session
                mock_driver.session = MagicMock(return_value=mock_session_cm)
                neo4j_client._driver = mock_driver

            mock_connect.side_effect = set_driver
            await neo4j_client.execute_query("MATCH (n) RETURN n")
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_node_success(self, neo4j_client):
        """Test successful node creation."""
        with patch.object(neo4j_client, "execute_query", new=AsyncMock()) as mock_exec:
            mock_node = create_mock_node(1, ["Test"], {"name": "Test Node"})
            mock_exec.return_value = [{"n": mock_node}]

            result = await neo4j_client.create_node(["Test"], {"name": "Test Node"})

            assert result["id"] == 1
            assert result["labels"] == ["Test"]
            assert result["properties"]["name"] == "Test Node"
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_node_success(self, neo4j_client):
        """Test successful node update."""
        with patch.object(neo4j_client, "execute_query", new=AsyncMock()) as mock_exec:
            mock_node = create_mock_node(1, ["Test"], {"name": "Updated"})
            mock_exec.return_value = [{"n": mock_node}]

            result = await neo4j_client.update_node(1, {"name": "Updated"})

            assert result["properties"]["name"] == "Updated"

    @pytest.mark.asyncio
    async def test_clear_database(self, neo4j_client):
        """Test clearing the database."""
        with patch.object(neo4j_client, "execute_query", new=AsyncMock()) as mock_exec:
            await neo4j_client.clear_database()
            mock_exec.assert_called_once_with(
                "MATCH (n) DETACH DELETE n", parameters=None, database=None
            )

    @pytest.mark.asyncio
    async def test_create_node_failure(self, neo4j_client):
        """Test node creation failure."""
        with patch.object(neo4j_client, "execute_query", new=AsyncMock()) as mock_exec:
            mock_exec.return_value = []  # No result

            with pytest.raises(ValueError, match="Failed to create node"):
                await neo4j_client.create_node(["Person"], {"name": "John"})

    @pytest.mark.asyncio
    async def test_get_nodes_success(self, neo4j_client):
        """Test successful node retrieval."""
        with patch.object(neo4j_client, "execute_query", new=AsyncMock()) as mock_exec:
            mock_node = create_mock_node(1, ["Person"], {"name": "John"})
            mock_exec.return_value = [{"n": mock_node}]

            result = await neo4j_client.get_nodes(["Person"])

            assert len(result) == 1
            assert result[0]["id"] == 1
            assert "Person" in result[0]["labels"]
            assert result[0]["properties"]["name"] == "John"
            mock_exec.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_nodes_with_properties(self, neo4j_client):
        """Test node retrieval with property filtering."""
        mock_driver = AsyncMock()
        mock_session_cm = AsyncMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_node = create_mock_node(1, ["Person"], {"name": "John"})

        mock_result.data.return_value = [{"n": mock_node}]
        mock_session.run.return_value = mock_result
        mock_session_cm.__aenter__.return_value = mock_session
        mock_driver.session = MagicMock(return_value=mock_session_cm)
        neo4j_client._driver = mock_driver

        result = await neo4j_client.get_nodes(
            labels=["Person"], properties={"name": "John"}, limit=10
        )

        assert len(result) == 1
        # Verify the query was constructed with WHERE clause
        call_args, call_kwargs = mock_session.run.call_args
        assert "WHERE" in call_args[0]
        assert "LIMIT" in call_args[0]

    @pytest.mark.asyncio
    async def test_update_node_not_found(self, neo4j_client):
        """Test node update when node not found."""
        mock_driver = AsyncMock()
        mock_session_cm = AsyncMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_result.data.return_value = []  # No result
        mock_session.run.return_value = mock_result
        mock_session_cm.__aenter__.return_value = mock_session
        mock_driver.session = MagicMock(return_value=mock_session_cm)
        neo4j_client._driver = mock_driver

        with pytest.raises(ValueError, match="Node with id 999 not found"):
            await neo4j_client.update_node(999, {"age": 25})

    @pytest.mark.asyncio
    async def test_delete_node_success(self, neo4j_client):
        """Test successful node deletion."""
        mock_driver = AsyncMock()
        mock_session_cm = AsyncMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_record = MagicMock()
        mock_record.__getitem__.return_value = 1  # deleted count
        mock_result.data.return_value = [mock_record]
        mock_session.run.return_value = mock_result
        mock_session_cm.__aenter__.return_value = mock_session
        mock_driver.session = MagicMock(return_value=mock_session_cm)
        neo4j_client._driver = mock_driver

        result = await neo4j_client.delete_node(1)

        assert result is True

    @pytest.mark.asyncio
    async def test_delete_node_not_found(self, neo4j_client):
        """Test node deletion when node not found."""
        mock_driver = AsyncMock()
        mock_session_cm = AsyncMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_record = MagicMock()
        mock_record.__getitem__.return_value = 0  # no nodes deleted
        mock_result.data.return_value = [mock_record]
        mock_session.run.return_value = mock_result
        mock_session_cm.__aenter__.return_value = mock_session
        mock_driver.session = MagicMock(return_value=mock_session_cm)
        neo4j_client._driver = mock_driver

        result = await neo4j_client.delete_node(999)

        assert result is False

    @pytest.mark.asyncio
    async def test_create_relationship_success(self, neo4j_client):
        """Test successful relationship creation."""
        mock_driver = AsyncMock()
        mock_session_cm = AsyncMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_rel = MagicMock()
        mock_rel.id = 1
        mock_rel.type = "KNOWS"
        mock_rel.items.return_value = {"since": "2023"}.items()

        mock_node_a = create_mock_node(1, ["Person"], {})
        mock_node_b = create_mock_node(2, ["Person"], {})

        mock_record = MagicMock()
        mock_record.__getitem__.side_effect = lambda key: {
            "a": mock_node_a,
            "r": mock_rel,
            "b": mock_node_b,
        }[key]
        mock_result.data.return_value = [mock_record]
        mock_session.run.return_value = mock_result
        mock_session_cm.__aenter__.return_value = mock_session
        mock_driver.session = MagicMock(return_value=mock_session_cm)
        neo4j_client._driver = mock_driver

        result = await neo4j_client.create_relationship(
            1, 2, "KNOWS", {"since": "2023"}
        )

        assert result["id"] == 1
        assert result["type"] == "KNOWS"
        assert result["from_node_id"] == 1
        assert result["to_node_id"] == 2

    @pytest.mark.asyncio
    async def test_get_relationships_success(self, neo4j_client):
        """Test successful relationship retrieval."""
        mock_driver = AsyncMock()
        mock_session_cm = AsyncMock()
        mock_session = AsyncMock()
        mock_result = AsyncMock()
        mock_rel = MagicMock()
        mock_rel.id = 1
        mock_rel.type = "KNOWS"
        mock_rel.items.return_value = {"since": "2023"}.items()

        mock_node_n = create_mock_node(1, ["Person"], {})
        mock_node_m = create_mock_node(2, ["Person"], {})

        mock_record = MagicMock()
        mock_record.__getitem__.side_effect = lambda key: {
            "n": mock_node_n,
            "r": mock_rel,
            "m": mock_node_m,
        }[key]
        mock_result.data.return_value = [mock_record]
        mock_session.run.return_value = mock_result
        mock_session_cm.__aenter__.return_value = mock_session
        mock_driver.session = MagicMock(return_value=mock_session_cm)
        neo4j_client._driver = mock_driver

        result = await neo4j_client.get_relationships(
            node_id=1, relationship_type="KNOWS"
        )

        assert len(result) == 1
        assert result[0]["id"] == 1
        assert result[0]["type"] == "KNOWS"

    @pytest.mark.asyncio
    async def test_get_graph_stats_success(self, neo4j_client):
        """Test successful graph statistics retrieval."""
        with patch.object(neo4j_client, "execute_query", new=AsyncMock()) as mock_exec:
            # Side effect for two separate calls
            mock_exec.side_effect = [
                [{"total_nodes": 5, "labels": ["Person", "Company"]}],  # Node stats
                [
                    {
                        "total_relationships": 3,
                        "relationship_types": ["KNOWS", "WORKS_FOR"],
                    }
                ],  # Rel stats
            ]

            result = await neo4j_client.get_graph_stats()

            assert result["total_nodes"] == 5
            assert result["total_relationships"] == 3
            assert "Person" in result["node_labels"]
            assert "KNOWS" in result["relationship_types"]
            assert mock_exec.call_count == 2

    @pytest.mark.asyncio
    async def test_get_graph_stats_error(self, neo4j_client):
        """Test graph statistics retrieval with error."""
        mock_driver = AsyncMock()
        mock_session_cm = AsyncMock()
        mock_session = AsyncMock()
        mock_session.run.side_effect = Exception("Database error")
        mock_session_cm.__aenter__.return_value = mock_session
        mock_driver.session = MagicMock(return_value=mock_session_cm)
        neo4j_client._driver = mock_driver

        result = await neo4j_client.get_graph_stats()

        # Should return error info instead of raising
        assert "error" in result
        assert result["total_nodes"] == 0
        assert result["total_relationships"] == 0

    @pytest.mark.asyncio
    async def test_auto_connect_on_operation(self, neo4j_client):
        """Test that client auto-connects when performing operations."""
        neo4j_client._driver = None  # Explicitly reset for this test

        async def mock_connect_side_effect():
            """Side effect to simulate driver initialization on connect."""
            mock_driver = AsyncMock()
            mock_session_cm = AsyncMock()
            mock_session = AsyncMock()
            mock_session.run.return_value = AsyncMock()
            mock_session_cm.__aenter__.return_value = mock_session
            mock_driver.session = MagicMock(return_value=mock_session_cm)
            neo4j_client._driver = mock_driver

        with patch.object(
            neo4j_client, "connect", side_effect=mock_connect_side_effect, autospec=True
        ) as mock_connect:
            await neo4j_client.execute_query("MATCH (n) RETURN n")
            mock_connect.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_node_returns_false(self, neo4j_client):
        with patch.object(
            neo4j_client, "execute_query", new=AsyncMock(return_value=[])
        ):
            result = await neo4j_client.delete_node(123)
            assert result is False

    @pytest.mark.asyncio
    async def test_create_relationship_failure(self, neo4j_client):
        with (
            patch.object(neo4j_client, "execute_query", new=AsyncMock(return_value=[])),
            pytest.raises(ValueError),
        ):
            await neo4j_client.create_relationship(1, 2, "KNOWS")

    @pytest.mark.asyncio
    async def test_clear_database_failure(self, neo4j_client):
        with patch.object(
            neo4j_client, "execute_query", new=AsyncMock(side_effect=Exception("fail"))
        ):
            result = await neo4j_client.clear_database()
            assert result is False


def test_workflow_manager_get_engine_unknown():
    manager = WorkflowManager()
    with pytest.raises(ValueError):
        manager.get_engine("unknown")


def test_workflow_manager_switch_engine_unknown():
    manager = WorkflowManager()
    with pytest.raises(ValueError):
        manager.switch_engine("unknown")


@pytest.mark.asyncio
async def test_crewai_engine_methods_raise():
    engine = CrewAIEngine()
    with pytest.raises(NotImplementedError):
        await engine.execute_workflow({})
    with pytest.raises(NotImplementedError):
        await engine.get_workflow_status("id")
    with pytest.raises(NotImplementedError):
        await engine.cancel_workflow("id")


@pytest.mark.asyncio
async def test_langgraph_engine_methods_raise():
    engine = LangGraphEngine()
    with pytest.raises(NotImplementedError):
        await engine.execute_workflow({})
    with pytest.raises(NotImplementedError):
        await engine.get_workflow_status("id")
    with pytest.raises(NotImplementedError):
        await engine.cancel_workflow("id")
