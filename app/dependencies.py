"""Dependency injection for core services and workflow engines."""

from typing import Literal

from fastapi import Depends

from app.config import settings
from app.core.mcp_client import MCPClient
from app.core.neo4j_client import Neo4jClient
from app.engines.crewai_engine import CrewAIEngine
from app.engines.langgraph_engine import LangGraphEngine

# Singleton instances
_neo4j_client = Neo4jClient()
_mcp_client = MCPClient()
_crewai_engine = CrewAIEngine(mcp_client=_mcp_client)
_langgraph_engine = LangGraphEngine(mcp_client=_mcp_client)


async def get_neo4j_client() -> Neo4jClient:
    return _neo4j_client


async def get_mcp_client() -> MCPClient:
    return _mcp_client


# Global workflow manager using dependency injection
class WorkflowManager:
    """Manages workflow execution and engine switching."""

    def __init__(
        self,
        crewai_engine: CrewAIEngine = Depends(lambda: _crewai_engine),
        langgraph_engine: LangGraphEngine = Depends(lambda: _langgraph_engine),
    ):
        self.crewai_engine = crewai_engine
        self.langgraph_engine = langgraph_engine
        self.current_engine: Literal["crewai", "langgraph"] = (
            settings.default_workflow_engine
        )

    def get_engine(self, engine_name: str | None = None):
        """Get the current or specified workflow engine."""
        engine = engine_name or self.current_engine
        if engine == "crewai":
            return self.crewai_engine
        elif engine == "langgraph":
            return self.langgraph_engine
        else:
            raise ValueError(f"Unknown engine: {engine}")

    def switch_engine(self, engine_name: str):
        """Switch the default workflow engine."""
        if engine_name not in ["crewai", "langgraph"]:
            raise ValueError(f"Unknown engine: {engine_name}")
        self.current_engine = engine_name  # type: ignore


_workflow_manager = WorkflowManager(
    crewai_engine=_crewai_engine, langgraph_engine=_langgraph_engine
)


async def get_workflow_manager() -> WorkflowManager:
    return _workflow_manager


async def get_workflow_engine(engine: str | None = None):
    engine = engine or settings.default_workflow_engine
    if engine == "crewai":
        return _crewai_engine
    elif engine == "langgraph":
        return _langgraph_engine
    else:
        raise ValueError(f"Unknown workflow engine: {engine}")
