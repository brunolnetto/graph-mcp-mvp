"""CrewAI workflow engine implementation."""

import contextlib
import logging
import uuid
from typing import Any

# Import CrewAI
from crewai import Agent
from crewai.tools import BaseTool

from app.core.mcp_client import MCPClient
from app.engines.base import WorkflowEngine
from app.engines.schemas import CrewAIWorkflowConfig, WorkflowDefinition


class MCPClientTool(BaseTool):
    def __init__(self, mcp_client: MCPClient, tool_name: str, arguments: dict):
        super().__init__(name=tool_name, description=f"MCPClient tool: {tool_name}")
        object.__setattr__(self, "_mcp_client", mcp_client)
        object.__setattr__(self, "_tool_name", tool_name)
        object.__setattr__(self, "_arguments", arguments)

    @property
    def mcp_client(self):
        return self._mcp_client

    @property
    def tool_name(self):
        return self._tool_name

    @property
    def arguments(self):
        return self._arguments

    def _run(self, *args, **kwargs):
        import asyncio

        loop = None
        with contextlib.suppress(RuntimeError):
            loop = asyncio.get_running_loop()
        if loop and loop.is_running():
            coro = self.mcp_client.call_tool(self.tool_name, self.arguments)
            return asyncio.run_coroutine_threadsafe(coro, loop).result()
        else:
            return asyncio.run(
                self.mcp_client.call_tool(self.tool_name, self.arguments)
            )


class CrewAIEngine(WorkflowEngine):
    """
    CrewAIEngine orchestrates a workflow using the real CrewAI library.
    Each task is assigned to a default agent, and MCPClient is wrapped as a CrewAI tool.
    """

    def __init__(self, mcp_client: MCPClient | None = None):
        self.mcp_client = mcp_client

    async def execute(self, workflow_config: dict[str, Any]) -> dict[str, Any]:
        config = CrewAIWorkflowConfig(**workflow_config)
        workflow_id = config.workflow_id or str(uuid.uuid4())
        results = {}
        errors = {}
        agents = {}
        tools = {}
        tasks = []
        logging.info(
            f"Starting CrewAI workflow {workflow_id} with {len(config.tasks)} tasks"
        )

        if not self.mcp_client:
            raise RuntimeError("MCPClient not provided to CrewAIEngine")

        # 1. Create agents and tools for each task
        for task_cfg in config.tasks:
            agent_name = f"agent_{task_cfg.name}"
            if agent_name not in agents:
                agents[agent_name] = Agent(
                    role=agent_name,
                    goal=f"Complete task {task_cfg.name}",
                    backstory=f"Agent for task {task_cfg.name}",
                    tools=[],
                )
            tool = MCPClientTool(self.mcp_client, task_cfg.tool, task_cfg.arguments)
            agents[agent_name].tools.append(tool)
            tools[task_cfg.name] = tool
            tasks.append((task_cfg.name, task_cfg.depends_on or []))

        # 2. Dependency resolution and simulated execution
        completed = set()
        failed = set()
        remaining = {name for name, _ in tasks}
        depends_map = dict(tasks)
        max_iterations = 2 * len(tasks) if tasks else 1
        iterations = 0
        while remaining:
            progress = False
            for name in list(remaining):
                depends_on = depends_map[name]
                if all(dep in completed for dep in depends_on):
                    try:
                        # Simulate running the task by calling the tool directly
                        result = tools[name]._run()
                        results[name] = result
                        completed.add(name)
                    except Exception as e:
                        errors[name] = str(e)
                        failed.add(name)
                    remaining.remove(name)
                    progress = True
                elif any(dep in failed for dep in depends_on):
                    errors[name] = "Dependencies not met"
                    failed.add(name)
                    remaining.remove(name)
                    progress = True
            iterations += 1
            if not progress or iterations > max_iterations:
                # Circular or unsatisfiable dependencies or runaway loop
                for name in remaining:
                    errors[name] = "Dependencies not met (circular or unsatisfiable)"
                break
        status = "failed" if errors else "completed"
        return {
            "workflow_id": workflow_id,
            "status": status,
            "results": results,
            "errors": errors,
        }

    async def execute_workflow(self, workflow: WorkflowDefinition) -> dict[str, Any]:
        # Convert canonical WorkflowDefinition to CrewAIWorkflowConfig
        crewai_tasks = [
            {
                "name": task.id,
                "tool": task.tool,
                "arguments": task.arguments,
                "depends_on": task.depends_on or [],
            }
            for task in workflow.tasks
        ]
        config = {
            "workflow_id": workflow.workflow_id,
            "tasks": crewai_tasks,
        }
        return await self.execute(config)

    async def get_workflow_status(self, workflow_id: str) -> dict[str, Any]:
        raise NotImplementedError("get_workflow_status must be implemented.")

    async def cancel_workflow(self, workflow_id: str) -> bool:
        raise NotImplementedError("cancel_workflow must be implemented.")

    @property
    def name(self):
        return "crewai"
