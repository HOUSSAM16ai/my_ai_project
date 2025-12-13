"""
HistoryService Facade
"""

from .application import HistoryServiceManager
from .infrastructure import InMemoryHistoryServiceRepository


class HistoryServiceFacade:
    """
    Facade for HistoryService
    Provides unified interface for all operations.
    """

    def __init__(self):
        self._repository = InMemoryHistoryServiceRepository()
        self._manager = HistoryServiceManager(self._repository)

    # Add your public methods here
