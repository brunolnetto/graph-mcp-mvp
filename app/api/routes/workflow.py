"""Workflow management API endpoints."""

from typing import Dict, List, Any, Optional, Literal
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.dependencies import get_workflow_manager
from app.dependencies import WorkflowManager

router = APIRouter(prefix="/workflow", tags=["workflow"])


class WorkflowConfig(BaseModel):
    """Model for workflow configuration."""
    name: str
    description: str
    tasks: List[Dict[str, Any]]
    engine: Optional[Literal["crewai", "langgraph"]] = None


class WorkflowResponse(BaseModel):
    """Model for workflow response."""
    workflow_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
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
        result = await engine.execute(config)
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
        ]
    )
    
    try:
        engine = manager.get_engine()
        result = await engine.execute(demo_config)
        return WorkflowResponse(
            workflow_id=result.get("workflow_id", "unknown"),
            status=result.get("status", "unknown"),
            result=result,
            engine=engine.name,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to run demo: {str(e)}")