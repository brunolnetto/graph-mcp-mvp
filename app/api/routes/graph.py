"""Graph operations API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.neo4j_client import Neo4jClient
from app.dependencies import get_neo4j_client

router = APIRouter(prefix="/graph", tags=["graph"])


class CypherQuery(BaseModel):
    """Request model for a Cypher query."""

    query: str = Field(..., min_length=1)
    parameters: dict[str, Any] | None = None


class NodeResponse(BaseModel):
    """Response model for a graph node."""

    id: int
    labels: list[str]
    properties: dict[str, Any]


class NodeCreate(BaseModel):
    """Request model for creating a node."""

    labels: list[str]
    properties: dict[str, Any]


class RelationshipCreate(BaseModel):
    """Model for creating a relationship."""
    from_node_id: int
    to_node_id: int
    relationship_type: str
    properties: dict[str, Any] | None = None


@router.post("/nodes", status_code=201)
async def create_node(
    node: NodeCreate,
    neo4j: Neo4jClient = Depends(get_neo4j_client),
):
    """Create a new node with given labels and properties."""
    try:
        new_node = await neo4j.create_node(node.labels, node.properties)
        return new_node
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nodes")
async def get_nodes(
    labels: list[str] = Query(None, description="List of labels to filter by"),
    properties: dict[str, Any] | None = None,
    limit: int = 100,
    neo4j: Neo4jClient = Depends(get_neo4j_client),
):
    """Get nodes by label and properties."""
    try:
        processed_labels = []
        if labels:
            for label_group in labels:
                processed_labels.extend(label_group.split(','))

        nodes = await neo4j.get_nodes(processed_labels or None, properties, limit)
        return nodes
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query")
async def execute_cypher(
    query: CypherQuery,
    neo4j: Neo4jClient = Depends(get_neo4j_client)
):
    """Execute a Cypher query."""
    try:
        result = await neo4j.execute_query(query.query, query.parameters)
        return {"result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute query: {str(e)}")


@router.put("/nodes/{node_id}")
async def update_node(
    node_id: int,
    properties: dict[str, Any],
    neo4j: Neo4jClient = Depends(get_neo4j_client),
):
    """Update a node's properties by its ID."""
    try:
        node = await neo4j.update_node(node_id, properties)
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        return node
    except ValueError as e: raise HTTPException(status_code=404, detail=str(e))
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


@router.delete("/nodes/{node_id}", status_code=204)
async def delete_node(
    node_id: int,
    neo4j: Neo4jClient = Depends(get_neo4j_client),
):
    """Delete a node by its ID."""
    try:
        success = await neo4j.delete_node(node_id)
        if success is not True:
            raise HTTPException(status_code=404, detail="Node not found")
        return {}
    except HTTPException: raise
    except ValueError as e: raise HTTPException(status_code=404, detail=str(e))
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))


@router.post("/relationships", status_code=201)
async def create_relationship(
    from_node_id: int,
    to_node_id: int,
    relationship_type: str,
    properties: dict[str, Any] | None = None,
    neo4j: Neo4jClient = Depends(get_neo4j_client),
):
    """Create a relationship between two nodes."""
    try:
        relationship = await neo4j.create_relationship(
            from_node_id, to_node_id, relationship_type, properties
        )
        if not relationship:
            raise HTTPException(
                status_code=404, detail="One or both nodes not found"
            )
        return relationship
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_graph_stats(neo4j: Neo4jClient = Depends(get_neo4j_client)):
    """Get statistics about the graph."""
    try:
        stats = await neo4j.get_graph_stats()
        return stats
    except Exception as e: raise HTTPException(status_code=500, detail=str(e))
