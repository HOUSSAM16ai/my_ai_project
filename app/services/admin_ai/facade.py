"""
AdminAi Facade
"""

from .application import AdminAiManager
from .infrastructure import InMemoryAdminAiRepository


class AdminAiFacade:
    """
    Facade for AdminAi
    Provides unified interface for all operations.
    """

    def __init__(self):
        self._repository = InMemoryAdminAiRepository()
        self._manager = AdminAiManager(self._repository)

    # Add your public methods here
