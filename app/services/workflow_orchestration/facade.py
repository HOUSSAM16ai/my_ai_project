"""
WorkflowOrchestration Facade
"""

from .application import WorkflowOrchestrationManager
from .infrastructure import InMemoryWorkflowOrchestrationRepository


class WorkflowOrchestrationFacade:
    """
    Facade for WorkflowOrchestration
    Provides unified interface for all operations.
    """

    def __init__(self):
        self._repository = InMemoryWorkflowOrchestrationRepository()
        self._manager = WorkflowOrchestrationManager(self._repository)

    # Add your public methods here
