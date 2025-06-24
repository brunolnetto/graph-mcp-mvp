"""LangGraph workflow engine implementation."""

import asyncio
import contextlib
import uuid
from collections.abc import Callable
from typing import Annotated, Any

from langgraph.errors import GraphRecursionError

# Import LangGraph
from langgraph.graph import END, StateGraph
from typing_extensions import TypedDict

from app.core.mcp_client import MCPClient
from app.engines.base import WorkflowEngine
from app.engines.schemas import (
    LangGraphNodeConfig,
    LangGraphWorkflowConfig,
    WorkflowDefinition,
)


# Reducers for state accumulation
def merge_dicts(a, b):
    out = dict(a or {})
    out.update(b or {})
    return out


def concat_lists(a, b):
    return (a or []) + (b or [])


class WorkflowState(TypedDict, total=False):
    results: Annotated[dict, merge_dicts]
    errors: Annotated[dict, merge_dicts]
    path: Annotated[list, concat_lists]


class LangGraphEngine(WorkflowEngine):
    """
    LangGraphEngine executes workflows as state machines/graphs using the real LangGraph library.
    Each node represents a task, and edges represent transitions.
    Uses MCPClient to call tools at each node.
    """

    def __init__(self, mcp_client: MCPClient | None = None):
        self.mcp_client = mcp_client

    @property
    def name(self):
        return "langgraph"

    async def execute(self, workflow_config: dict[str, Any]) -> dict[str, Any]:
        try:
            config = LangGraphWorkflowConfig(**workflow_config)
            workflow_id = config.workflow_id or str(uuid.uuid4())
            node_map = {node.id: node for node in config.nodes}

            if not self.mcp_client:
                # Return error for missing MCPClient
                start_node = (
                    config.start_node if hasattr(config, "start_node") else None
                )
                return {
                    "workflow_id": workflow_id,
                    "status": "failed",
                    "path": [start_node] if start_node else [],
                    "results": {},
                    "errors": (
                        {start_node: "MCPClient not provided to LangGraphEngine"}
                        if start_node
                        else {"error": "MCPClient not provided to LangGraphEngine"}
                    ),
                }

            # Use WorkflowState TypedDict with reducers
            graph = StateGraph(WorkflowState)

            # Node functions: each node calls the MCPClient tool
            def make_node_func(node_id: str) -> Callable[[dict], dict]:
                def node_func(_state: dict) -> dict:
                    node: LangGraphNodeConfig = node_map[node_id]
                    try:
                        # Run async MCPClient call in the current event loop
                        loop = None
                        with contextlib.suppress(RuntimeError):
                            loop = asyncio.get_running_loop()
                        if loop and loop.is_running():
                            coro = self.mcp_client.call_tool(node.tool, node.arguments)  # type: ignore[attr-defined]
                            result = asyncio.run_coroutine_threadsafe(
                                coro, loop
                            ).result()
                        else:
                            result = asyncio.run(self.mcp_client.call_tool(node.tool, node.arguments))  # type: ignore[attr-defined]
                        update = {
                            "results": {node_id: result},
                            "path": [node_id],
                        }
                    except Exception as e:
                        update = {
                            "errors": {node_id: str(e)},
                            "path": [node_id],
                        }
                    print(f"NODE {node_id} UPDATE: {update}")
                    return update

                return node_func

            # Build the graph
            graph = StateGraph(WorkflowState)
            # Add nodes
            for node_id in node_map:
                graph.add_node(node_id, make_node_func(node_id))
            # Add edges (including conditional edges)
            edge_map = {}
            for edge in config.edges:
                edge_map.setdefault(edge.from_node, []).append(edge)

            for from_node, edges in edge_map.items():
                # If any edge has a condition, use conditional edges
                if any(edge.condition for edge in edges):

                    def make_cond_func(edges, from_node=from_node):
                        def cond(state: dict) -> str:
                            results = state.get("results", {})
                            current_node_id = (
                                state.get("path", [])[-1]
                                if state.get("path")
                                else from_node
                            )
                            for edge in edges:
                                cond_str = edge.condition
                                if cond_str:
                                    try:
                                        if eval(
                                            cond_str,
                                            {},
                                            {
                                                "results": results,
                                                "current_node_id": current_node_id,
                                            },
                                        ):
                                            return edge.to_node
                                    except Exception:
                                        continue
                                else:
                                    return edge.to_node
                            # If no edge matches, return END (will be handled as error)
                            return END

                        return cond

                    cond_func = make_cond_func(edges)
                    # Map all possible to_nodes to themselves, plus END
                    path_map = {edge.to_node: edge.to_node for edge in edges}
                    path_map[END] = END
                    graph.add_conditional_edges(from_node, cond_func, path_map)
                else:
                    # Only unconditional edges
                    for edge in edges:
                        graph.add_edge(from_node, edge.to_node)
            # Set entry and finish points
            graph.set_entry_point(config.start_node)
            for node_id in node_map:
                # If a node has no outgoing edges, mark as finish
                if node_id not in edge_map:
                    graph.set_finish_point(node_id)
            # Compile the graph
            compiled = graph.compile()
            # Initial state
            initial_state = {"results": {}, "errors": {}, "path": []}
            # Run the graph (async)
            state = await compiled.ainvoke(initial_state)
            print(f"FINAL STATE AFTER WORKFLOW EXEC: {state}")
            # If any node set __error__, mark as failed
            if not state:
                return {
                    "workflow_id": workflow_id,
                    "status": "failed",
                    "path": [],
                    "results": {},
                    "errors": {
                        "error": "Workflow execution failed with no state returned"
                    },
                }
            status = "failed" if state.get("errors") else "completed"
            return {
                "workflow_id": workflow_id,
                "status": status,
                "path": state.get("path", []),
                "results": state.get("results", {}),
                "errors": state.get("errors", {}),
            }
        except (ValueError, GraphRecursionError, AttributeError) as e:
            # Handle LangGraph and validation errors
            workflow_id = workflow_config.get("workflow_id") or str(uuid.uuid4())
            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "path": [],
                "results": {},
                "errors": {"error": str(e)},
            }
        except Exception as e:
            workflow_id = workflow_config.get("workflow_id") or str(uuid.uuid4())
            return {
                "workflow_id": workflow_id,
                "status": "failed",
                "path": [],
                "results": {},
                "errors": {"error": str(e)},
            }

    async def execute_workflow(self, workflow: WorkflowDefinition) -> dict[str, Any]:
        # Convert canonical WorkflowDefinition to LangGraphWorkflowConfig
        nodes = [
            {
                "id": task.id,
                "tool": task.tool,
                "arguments": task.arguments,
            }
            for task in workflow.tasks
        ]
        # Edges: for each task, create edges from dependencies to this task
        edges = []
        for task in workflow.tasks:
            for dep in task.depends_on:
                edges.append({"from_node": dep, "to_node": task.id})
        # Start node: first task with no dependencies, or first task
        start_node = next(
            (task.id for task in workflow.tasks if not task.depends_on),
            workflow.tasks[0].id if workflow.tasks else None,
        )
        config = {
            "workflow_id": workflow.workflow_id,
            "nodes": nodes,
            "edges": edges,
            "start_node": start_node,
        }
        return await self.execute(config)

    async def get_workflow_status(self, workflow_id: str) -> dict[str, Any]:
        raise NotImplementedError("get_workflow_status must be implemented.")

    async def cancel_workflow(self, workflow_id: str) -> bool:
        raise NotImplementedError("cancel_workflow must be implemented.")
