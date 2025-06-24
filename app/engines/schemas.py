from typing import Any

from pydantic import BaseModel, Field


# CrewAI workflow config
class CrewAITaskConfig(BaseModel):
    name: str
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] | None = None  # List of task names this task depends on


class CrewAIWorkflowConfig(BaseModel):
    workflow_id: str | None = None
    tasks: list[CrewAITaskConfig]


# LangGraph workflow config
class LangGraphNodeConfig(BaseModel):
    id: str
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)


class LangGraphEdgeConfig(BaseModel):
    from_node: str
    to_node: str
    condition: str | None = None  # Optional condition for transition


class LangGraphWorkflowConfig(BaseModel):
    workflow_id: str | None = None
    nodes: list[LangGraphNodeConfig]
    edges: list[LangGraphEdgeConfig]
    start_node: str


# Canonical, engine-agnostic workflow schema
class WorkflowTask(BaseModel):
    id: str
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    depends_on: list[str] = []


class WorkflowDefinition(BaseModel):
    workflow_id: str | None = None
    tasks: list[WorkflowTask]
