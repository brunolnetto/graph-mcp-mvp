"""Workflow management API endpoints."""

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, model_validator

from app.dependencies import WorkflowManager, get_workflow_manager

router = APIRouter(prefix="/workflow", tags=["workflow"])


class WorkflowConfig(BaseModel):
    """Model for workflow configuration. Supports both CrewAI and LangGraph engines."""
    name: str
    description: str
    # CrewAI fields
    tasks: list[dict[str, Any]] | None = None
    # LangGraph fields
    nodes: list[dict[str, Any]] | None = None
    edges: list[dict[str, Any]] | None = None
    start_node: str | None = None
    engine: Literal["crewai", "langgraph"] | None = None

    @model_validator(mode="after")
    def validate_for_engine(self):
        if self.engine == "crewai":
            if not self.tasks:
                raise ValueError("'tasks' is required for CrewAI engine")
        elif self.engine == "langgraph":
            if not (self.nodes and self.edges and self.start_node):
                raise ValueError("'nodes', 'edges', and 'start_node' are required for LangGraph engine")
        else:
            raise ValueError("'engine' must be either 'crewai' or 'langgraph'")
        return self


class WorkflowResponse(BaseModel):
    """Model for workflow response."""
    workflow_id: str
    status: str
    result: dict[str, Any] | None = None
    engine: str


class EngineSwitch(BaseModel):
    """Model for switching workflow engines."""
    engine: Literal["crewai", "langgraph"]


@router.post("/execute", response_model=WorkflowResponse)
async def execute_workflow(
    config: WorkflowConfig,
    manager: WorkflowManager = Depends(get_workflow_manager)
):
    """Execute a workflow with the specified or default engine."""
    try:
        engine = manager.get_engine(config.engine)
        result = await engine.execute(config.model_dump())
        return WorkflowResponse(
            workflow_id=result.get("workflow_id", "unknown"),
            status=result.get("status", "unknown"),
            result=result,
            engine=engine.name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute workflow: {str(e)}")


@router.get("/engines")
async def list_engines(manager: WorkflowManager = Depends(get_workflow_manager)):
    """List available workflow engines."""
    return {
        "available_engines": ["crewai", "langgraph"],
        "current_engine": manager.current_engine,
        "descriptions": {
            "crewai": "Multi-agent framework for complex workflows",
            "langgraph": "Stateful, multi-actor applications with LLMs"
        }
    }


@router.put("/engine")
async def switch_engine(
    engine_switch: EngineSwitch,
    manager: WorkflowManager = Depends(get_workflow_manager)
):
    """Switch the default workflow engine."""
    try:
        manager.switch_engine(engine_switch.engine)
        return {
            "message": f"Switched to {engine_switch.engine}",
            "current_engine": manager.current_engine
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to switch engine: {str(e)}")


@router.get("/engine/current")
async def get_current_engine(manager: WorkflowManager = Depends(get_workflow_manager)):
    """Get the current workflow engine."""
    if manager.current_engine is None:
        raise HTTPException(status_code=500, detail="Current engine is not set.")
    return {
        "current_engine": manager.current_engine,
        "engine_info": {
            "crewai": "Multi-agent framework for complex workflows",
            "langgraph": "Stateful, multi-actor applications with LLMs"
        }[manager.current_engine]
    }


@router.post("/demo")
async def run_demo_workflow(manager: WorkflowManager = Depends(get_workflow_manager)):
    """Run a demo workflow to showcase the current engine."""
    demo_config = WorkflowConfig(
        name="Demo Workflow",
        description="A demonstration workflow showcasing the current engine",
        tasks=[
            {"name": "Data Collection", "type": "research"},
            {"name": "Analysis", "type": "processing"},
            {"name": "Report Generation", "type": "output"}
        ],
        engine="crewai"
    )

    try:
        engine = manager.get_engine()
        result = await engine.execute(demo_config.model_dump())
        return WorkflowResponse(
            workflow_id=result.get("workflow_id", "unknown"),
            status=result.get("status", "unknown"),
            result=result,
            engine=engine.name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run demo: {str(e)}")
