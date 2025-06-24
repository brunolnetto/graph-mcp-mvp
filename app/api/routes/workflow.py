"""Workflow management API endpoints."""

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.dependencies import WorkflowManager, get_workflow_manager
from app.engines.schemas import WorkflowDefinition, WorkflowTask

router = APIRouter(prefix="/workflow", tags=["workflow"])


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
    workflow: WorkflowDefinition,
    engine_name: str | None = None,
    manager: WorkflowManager = Depends(get_workflow_manager),
):
    """Execute a workflow with the specified or default engine."""
    try:
        engine = manager.get_engine(engine_name)
        result = await engine.execute_workflow(workflow)
        return WorkflowResponse(
            workflow_id=result.get("workflow_id", "unknown"),
            status=result.get("status", "unknown"),
            result=result,
            engine=engine.name,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to execute workflow: {str(e)}"
        ) from e


@router.get("/engines")
async def list_engines(manager: WorkflowManager = Depends(get_workflow_manager)):
    """List available workflow engines."""
    return {
        "available_engines": ["crewai", "langgraph"],
        "current_engine": manager.current_engine,
        "descriptions": {
            "crewai": "Multi-agent framework for complex workflows",
            "langgraph": "Stateful, multi-actor applications with LLMs",
        },
    }


@router.put("/engine")
async def switch_engine(
    engine_switch: EngineSwitch,
    manager: WorkflowManager = Depends(get_workflow_manager),
):
    """Switch the default workflow engine."""
    try:
        manager.switch_engine(engine_switch.engine)
        return {
            "message": f"Switched to {engine_switch.engine}",
            "current_engine": manager.current_engine,
        }
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Failed to switch engine: {str(e)}"
        ) from e


@router.get("/engine/current")
async def get_current_engine(manager: WorkflowManager = Depends(get_workflow_manager)):
    """Get the current workflow engine."""
    if manager.current_engine is None:
        raise HTTPException(status_code=500, detail="Current engine is not set.")
    return {
        "current_engine": manager.current_engine,
        "engine_info": {
            "crewai": "Multi-agent framework for complex workflows",
            "langgraph": "Stateful, multi-actor applications with LLMs",
        }[manager.current_engine],
    }


@router.post("/demo")
async def run_demo_workflow(manager: WorkflowManager = Depends(get_workflow_manager)):
    """Run a demo workflow to showcase the current engine."""
    demo_workflow = WorkflowDefinition(
        workflow_id="demo-1",
        tasks=[
            WorkflowTask(
                id="data_collection", tool="research_tool", arguments={}, depends_on=[]
            ),
            WorkflowTask(
                id="analysis",
                tool="processing_tool",
                arguments={},
                depends_on=["data_collection"],
            ),
            WorkflowTask(
                id="report_generation",
                tool="output_tool",
                arguments={},
                depends_on=["analysis"],
            ),
        ],
    )
    try:
        engine = manager.get_engine()
        result = await engine.execute_workflow(demo_workflow)
        return WorkflowResponse(
            workflow_id=result.get("workflow_id", "unknown"),
            status=result.get("status", "unknown"),
            result=result,
            engine=engine.name,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to run demo: {str(e)}"
        ) from e
