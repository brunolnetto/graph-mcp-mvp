"""Neo4j client for graph database operations."""

import logging
from typing import Any

from neo4j import AsyncGraphDatabase
from neo4j.exceptions import AuthError, ClientError, ServiceUnavailable

from app.config import settings


class Neo4jClient:
    """Async Neo4j client with connection pooling and error handling."""

    def __init__(
        self,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
        database: str | None = None,
    ):
        """Initialize Neo4j client."""
        self.uri = uri or settings.neo4j_uri
        self.user = user or settings.neo4j_user
        self.password = password or settings.neo4j_password
        self.database = database or settings.neo4j_database
        self._driver = None

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def connect(self):
        """Establish connection to Neo4j."""
        try:
            self._driver = AsyncGraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
            # Verify connection
            await self._driver.verify_connectivity()
            logging.info(f"Connected to Neo4j at {self.uri}")
        except (ServiceUnavailable, AuthError) as e:
            logging.error(f"Failed to connect to Neo4j: {e}")
            raise

    async def close(self):
        """Close Neo4j connection."""
        if self._driver:
            await self._driver.close()
            self._driver = None
            logging.info("Neo4j connection closed")

    async def execute_query(
        self,
        query: str,
        parameters: dict[str, Any] | None = None,
        database: str | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a Cypher query."""
        if not self._driver:
            await self.connect()
        if not self._driver:
            raise RuntimeError("Neo4j driver is not initialized.")
        try:
            async with self._driver.session(
                database=database or self.database
            ) as session:
                result = await session.run(query, parameters or {})
                records = await result.data()
                return records
        except ClientError as e:
            logging.error(f"Cypher query failed: {e}")
            raise
        except Exception as e:
            logging.error(f"Unexpected error executing query: {e}")
            raise

    async def create_node(
        self, labels: list[str], properties: dict[str, Any], database: str | None = None
    ) -> dict[str, Any]:
        """Create a node with specified labels and properties."""
        labels_str = ":".join(labels)

        # Correctly format properties for the CREATE clause
        properties_str = ", ".join([f"{k}: ${k}" for k in properties])

        query = f"""
        CREATE (n:{labels_str} {{{properties_str}}})
        RETURN n
        """

        result = await self.execute_query(query, properties, database)
        if result:
            node = result[0]["n"]
            return {
                "id": node.id,
                "labels": list(node.labels),
                "properties": dict(node),
            }
        raise ValueError("Failed to create node")

    async def get_nodes(
        self,
        labels: list[str] | None = None,
        properties: dict[str, Any] | None = None,
        limit: int | None = None,
        database: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get nodes with optional filtering."""
        if labels:
            labels_str = ":".join(labels)
            query = f"MATCH (n:{labels_str})"
        else:
            query = "MATCH (n)"

        if properties:
            conditions = [f"n.{k} = ${k}" for k in properties]
            query += f" WHERE {' AND '.join(conditions)}"

        query += " RETURN n"

        if limit:
            query += f" LIMIT {limit}"

        result = await self.execute_query(query, properties, database)
        return [
            {
                "id": record["n"].id,
                "labels": list(record["n"].labels),
                "properties": dict(record["n"]),
            }
            for record in result
        ]

    async def update_node(
        self, node_id: int, properties: dict[str, Any], database: str | None = None
    ) -> dict[str, Any]:
        """Update node properties."""
        properties_str = ", ".join([f"n.{k} = ${k}" for k in properties])

        query = f"""
        MATCH (n) WHERE id(n) = $node_id
        SET {properties_str}
        RETURN n
        """

        params = {"node_id": node_id, **properties}
        result = await self.execute_query(query, params, database)

        if result:
            node = result[0]["n"]
            return {
                "id": node.id,
                "labels": list(node.labels),
                "properties": dict(node),
            }
        raise ValueError(f"Node with id {node_id} not found")

    async def delete_node(self, node_id: int, database: str | None = None) -> bool:
        """Delete a node by ID."""
        query = """
        MATCH (n) WHERE id(n) = $node_id
        DETACH DELETE n
        RETURN count(n) as deleted
        """

        result = await self.execute_query(query, {"node_id": node_id}, database)
        return result[0]["deleted"] > 0 if result else False

    async def create_relationship(
        self,
        from_node_id: int,
        to_node_id: int,
        relationship_type: str,
        properties: dict[str, Any] | None = None,
        database: str | None = None,
    ) -> dict[str, Any]:
        """Create a relationship between two nodes."""
        properties_str = ""
        if properties:
            properties_str = ", " + ", ".join([f"r.{k} = ${k}" for k in properties])

        query = f"""
        MATCH (a), (b)
        WHERE id(a) = $from_id AND id(b) = $to_id
        CREATE (a)-[r:{relationship_type}{properties_str}]->(b)
        RETURN a, r, b
        """

        params = {"from_id": from_node_id, "to_id": to_node_id, **(properties or {})}
        result = await self.execute_query(query, params, database)

        if result:
            rel = result[0]["r"]
            return {
                "id": rel.id,
                "type": rel.type,
                "properties": dict(rel),
                "from_node_id": result[0]["a"].id,
                "to_node_id": result[0]["b"].id,
            }
        raise ValueError("Failed to create relationship")

    async def get_relationships(
        self,
        node_id: int | None = None,
        relationship_type: str | None = None,
        direction: str = "both",
        database: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get relationships with optional filtering."""
        if node_id:
            if direction == "outgoing":
                query = "MATCH (n)-[r]->(m) WHERE id(n) = $node_id"
            elif direction == "incoming":
                query = "MATCH (n)<-[r]-(m) WHERE id(n) = $node_id"
            else:
                query = "MATCH (n)-[r]-(m) WHERE id(n) = $node_id"
        else:
            query = "MATCH (n)-[r]-(m)"

        if relationship_type:
            query += " AND type(r) = $rel_type"

        query += " RETURN n, r, m"

        params = {}
        if node_id:
            params["node_id"] = node_id
        if relationship_type:
            params["rel_type"] = relationship_type

        result = await self.execute_query(query, params, database)
        return [
            {
                "id": record["r"].id,
                "type": record["r"].type,
                "properties": dict(record["r"]),
                "from_node": record["n"].id,
                "to_node": record["m"].id,
            }
            for record in result
        ]

    async def get_graph_stats(self, database: str | None = None) -> dict[str, Any]:
        """Get graph statistics."""
        stats_query = """
        MATCH (n)
        RETURN count(n) as total_nodes,
               labels(n) as labels
        """

        rel_stats_query = """
        MATCH ()-[r]->()
        RETURN count(r) as total_relationships,
               collect(distinct type(r)) as relationship_types
        """

        try:
            node_stats = await self.execute_query(stats_query, database=database)
            rel_stats = await self.execute_query(rel_stats_query, database=database)

            # Process labels
            all_labels = []
            for record in node_stats:
                all_labels.extend(record["labels"])

            unique_labels = list(set(all_labels))

            return {
                "total_nodes": node_stats[0]["total_nodes"] if node_stats else 0,
                "total_relationships": (
                    rel_stats[0]["total_relationships"] if rel_stats else 0
                ),
                "node_labels": unique_labels,
                "relationship_types": (
                    rel_stats[0]["relationship_types"] if rel_stats else []
                ),
                "database": "Neo4j",
                "uri": self.uri,
            }
        except Exception as e:
            logging.error(f"Failed to get graph stats: {e}")
            return {
                "total_nodes": 0,
                "total_relationships": 0,
                "node_labels": [],
                "relationship_types": [],
                "database": "Neo4j",
                "uri": self.uri,
                "error": str(e),
            }

    async def clear_database(self, database: str | None = None) -> bool:
        """Clear all data from the database (use with caution!)."""
        query = "MATCH (n) DETACH DELETE n"
        try:
            await self.execute_query(query, parameters=None, database=database)
            logging.warning(f"Database {database or self.database} cleared")
            return True
        except Exception as e:
            logging.error(f"Failed to clear database: {e}")
            return False

    async def shortest_path(
        self, source_id: int, target_id: int, relationship: str = "CONNECTED"
    ) -> list[int]:
        # Use Cypher to find the shortest path between two nodes
        query = (
            "MATCH (start), (end) "
            "WHERE start.id = $source_id AND end.id = $target_id "
            "MATCH path = shortestPath((start)-[:" + relationship + "*]-(end)) "
            "RETURN [n IN nodes(path) | n.id] AS node_ids"
        )
        result = await self.execute_query(
            query, {"source_id": source_id, "target_id": target_id}
        )
        if result and result[0].get("node_ids"):
            return result[0]["node_ids"]
        return []


# Global client instance
neo4j_client = Neo4jClient()
