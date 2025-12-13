"""
ApiObservability Facade
"""

from .application import ApiObservabilityManager
from .infrastructure import InMemoryApiObservabilityRepository


class ApiObservabilityFacade:
    """
    Facade for ApiObservability
    Provides unified interface for all operations.
    """

    def __init__(self):
        self._repository = InMemoryApiObservabilityRepository()
        self._manager = ApiObservabilityManager(self._repository)

    # Add your public methods here
