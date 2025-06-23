"""CrewAI workflow engine implementation."""

from typing import Any
from app.core.mcp_client import MCPClient
from app.engines.schemas import CrewAIWorkflowConfig, CrewAITaskConfig
import uuid
import logging


class CrewAIEngine:
    """
    CrewAIEngine orchestrates a linear workflow using the provided configuration.
    Each task is executed in order, using MCPClient to call external tools.
    """
    def __init__(self, mcp_client: MCPClient | None = None):
        self.mcp_client = mcp_client

    async def execute(self, workflow_config: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a workflow based on the provided configuration.
        Steps:
        1. Validate and parse the workflow config.
        2. For each task, use MCPClient to call the required tool.
        3. Aggregate and return results.
        """
        # 1. Validate and parse config
        config = CrewAIWorkflowConfig(**workflow_config)
        workflow_id = config.workflow_id or str(uuid.uuid4())
        results = {}
        errors = {}
        completed = set()
        task_map = {task.name: task for task in config.tasks}
        ordered_tasks = self._resolve_task_order(config.tasks)
        logging.info(f"Starting CrewAI workflow {workflow_id} with {len(ordered_tasks)} tasks")

        # 2. Orchestrate tasks in order
        for task_name in ordered_tasks:
            task: CrewAITaskConfig = task_map[task_name]
            # Check dependencies
            if task.depends_on:
                if not all(dep in completed for dep in task.depends_on):
                    errors[task.name] = f"Dependencies not met: {task.depends_on}"
                    continue
            try:
                # 3. Call MCPClient for each task
                if not self.mcp_client:
                    raise RuntimeError("MCPClient not provided to CrewAIEngine")
                result = await self.mcp_client.call_tool(task.tool, task.arguments)
                results[task.name] = result
                completed.add(task.name)
                logging.info(f"Task {task.name} completed successfully")
            except Exception as e:
                errors[task.name] = str(e)
                logging.error(f"Task {task.name} failed: {e}")

        # After resolving order, check for missing dependencies
        if getattr(self, 'missing_dependencies', None):
            for missing in self.missing_dependencies:
                errors[missing] = f"Task dependency '{missing}' not found in workflow."

        status = "completed" if not errors else "failed"
        return {
            "workflow_id": workflow_id,
            "status": status,
            "results": results,
            "errors": errors,
        }

    def _resolve_task_order(self, tasks: list[CrewAITaskConfig]) -> list[str]:
        # Simple topological sort to respect dependencies
        order = []
        visited = set()
        task_map = {task.name: task for task in tasks}
        self.missing_dependencies = set()

        def visit(name):
            if name in visited:
                return
            visited.add(name)
            task = task_map.get(name)
            if not task:
                self.missing_dependencies.add(name)
                return
            if task.depends_on:
                for dep in task.depends_on:
                    visit(dep)
            order.append(name)

        for task in tasks:
            visit(task.name)
        return order

    async def get_workflow_status(self, workflow_id: str) -> dict[str, Any]:
        raise NotImplementedError("CrewAIEngine.get_workflow_status is not implemented yet.")

    async def cancel_workflow(self, workflow_id: str) -> bool:
        raise NotImplementedError("CrewAIEngine.cancel_workflow is not implemented yet.")

    async def execute_workflow(self, workflow_config: Any) -> dict[str, Any]:
        raise NotImplementedError("CrewAIEngine.execute_workflow is not implemented yet.")

    @property
    def name(self):
        return "crewai"

    # Optionally, add more helper methods for task orchestration, error handling, etc.
