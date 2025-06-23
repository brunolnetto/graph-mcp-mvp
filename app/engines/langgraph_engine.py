"""LangGraph workflow engine implementation."""

from typing import Any
from app.core.mcp_client import MCPClient
from app.engines.schemas import LangGraphWorkflowConfig, LangGraphNodeConfig, LangGraphEdgeConfig
import uuid
import logging

from app.engines.base import WorkflowEngine


class LangGraphEngine(WorkflowEngine):
    """
    LangGraphEngine executes workflows as state machines/graphs.
    Each node represents a task, and edges represent transitions.
    Uses MCPClient to call tools at each node.
    """
    def __init__(self, mcp_client: MCPClient | None = None):
        self.mcp_client = mcp_client

    async def execute(self, workflow_config: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a workflow as a state machine/graph.
        Steps:
        1. Validate and parse the workflow config (nodes, edges).
        2. Traverse the graph/state machine, executing tasks at each node.
        3. Use MCPClient to call tools at each node.
        4. Aggregate and return results.
        """
        config = LangGraphWorkflowConfig(**workflow_config)
        workflow_id = config.workflow_id or str(uuid.uuid4())
        node_map = {node.id: node for node in config.nodes}
        edge_map = self._build_edge_map(config.edges)
        results = {}
        errors = {}
        path = []
        current_node_id = config.start_node
        visited = set()
        logging.info(f"Starting LangGraph workflow {workflow_id} at node {current_node_id}")

        while current_node_id:
            if current_node_id in visited:
                errors[current_node_id] = "Cycle detected in workflow graph"
                logging.error(f"Cycle detected at node {current_node_id}")
                break
            visited.add(current_node_id)
            if current_node_id not in node_map:
                errors[current_node_id] = f"Node '{current_node_id}' not found in workflow."
                logging.error(f"Node '{current_node_id}' not found in workflow.")
                break
            node: LangGraphNodeConfig = node_map[current_node_id]
            path.append(current_node_id)
            try:
                if not self.mcp_client:
                    raise RuntimeError("MCPClient not provided to LangGraphEngine")
                result = await self.mcp_client.call_tool(node.tool, node.arguments)
                results[current_node_id] = result
                logging.info(f"Node {current_node_id} executed successfully")
            except Exception as e:
                errors[current_node_id] = str(e)
                logging.error(f"Node {current_node_id} failed: {e}")
                break  # Stop on error for now
            # Determine next node
            next_node_id = None
            for edge in edge_map.get(current_node_id, []):
                # TODO: Evaluate edge.condition if present (for now, just take the first edge)
                next_node_id = edge.to_node
                break
            current_node_id = next_node_id

        status = "completed" if not errors else "failed"
        return {
            "workflow_id": workflow_id,
            "status": status,
            "path": path,
            "results": results,
            "errors": errors,
        }

    def _build_edge_map(self, edges: list[LangGraphEdgeConfig]) -> dict[str, list[LangGraphEdgeConfig]]:
        edge_map = {}
        for edge in edges:
            edge_map.setdefault(edge.from_node, []).append(edge)
        return edge_map

    async def execute_workflow(self, workflow_config: Any) -> dict[str, Any]:
        raise NotImplementedError("LangGraphEngine.execute_workflow is not implemented yet.")

    async def get_workflow_status(self, workflow_id: str) -> dict[str, Any]:
        raise NotImplementedError("LangGraphEngine.get_workflow_status is not implemented yet.")

    async def cancel_workflow(self, workflow_id: str) -> bool:
        raise NotImplementedError("LangGraphEngine.cancel_workflow is not implemented yet.")

    @property
    def name(self):
        return "langgraph"

    # Optionally, add more helper methods for graph traversal, error handling, etc.
