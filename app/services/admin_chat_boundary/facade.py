"""
AdminChatBoundary Facade
"""

from .application import AdminChatBoundaryManager
from .infrastructure import InMemoryAdminChatBoundaryRepository


class AdminChatBoundaryFacade:
    """
    Facade for AdminChatBoundary
    Provides unified interface for all operations.
    """

    def __init__(self):
        self._repository = InMemoryAdminChatBoundaryRepository()
        self._manager = AdminChatBoundaryManager(self._repository)

    # Add your public methods here
