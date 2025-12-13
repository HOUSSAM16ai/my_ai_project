"""
AdminChatPerformance Facade
"""

from .application import AdminChatPerformanceManager
from .infrastructure import InMemoryAdminChatPerformanceRepository


class AdminChatPerformanceFacade:
    """
    Facade for AdminChatPerformance
    Provides unified interface for all operations.
    """

    def __init__(self):
        self._repository = InMemoryAdminChatPerformanceRepository()
        self._manager = AdminChatPerformanceManager(self._repository)

    # Add your public methods here
