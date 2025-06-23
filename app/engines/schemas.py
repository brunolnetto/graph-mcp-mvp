from typing import Any, List, Optional, Dict
from pydantic import BaseModel, Field
from typing_extensions import Literal

# CrewAI workflow config
class CrewAITaskConfig(BaseModel):
    name: str
    tool: str
    arguments: Dict[str, Any] = Field(default_factory=dict)
    depends_on: Optional[List[str]] = None  # List of task names this task depends on

class CrewAIWorkflowConfig(BaseModel):
    workflow_id: Optional[str] = None
    tasks: List[CrewAITaskConfig]

# LangGraph workflow config
class LangGraphNodeConfig(BaseModel):
    id: str
    tool: str
    arguments: Dict[str, Any] = Field(default_factory=dict)

class LangGraphEdgeConfig(BaseModel):
    from_node: str
    to_node: str
    condition: Optional[str] = None  # Optional condition for transition

class LangGraphWorkflowConfig(BaseModel):
    workflow_id: Optional[str] = None
    nodes: List[LangGraphNodeConfig]
    edges: List[LangGraphEdgeConfig]
    start_node: str 