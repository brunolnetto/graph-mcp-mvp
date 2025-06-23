"""Abstract base class for workflow engines."""

from abc import ABC, abstractmethod
from typing import Any, Dict

class WorkflowEngine(ABC):
    @abstractmethod
    async def execute_workflow(self, workflow_config: Any) -> Dict[str, Any]:
        """Execute a workflow and return the result."""
        pass

    @abstractmethod
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get the status of a workflow by ID."""
        pass

    @abstractmethod
    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow by ID."""
        pass 