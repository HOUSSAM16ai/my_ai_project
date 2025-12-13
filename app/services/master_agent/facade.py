"""
MasterAgent Facade
"""

from .application import MasterAgentManager
from .infrastructure import InMemoryMasterAgentRepository


class MasterAgentFacade:
    """
    Facade for MasterAgent
    Provides unified interface for all operations.
    """

    def __init__(self):
        self._repository = InMemoryMasterAgentRepository()
        self._manager = MasterAgentManager(self._repository)

    # Add your public methods here
