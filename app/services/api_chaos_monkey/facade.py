"""
ApiChaosMonkey Facade
"""

from .application import ApiChaosMonkeyManager
from .infrastructure import InMemoryApiChaosMonkeyRepository


class ApiChaosMonkeyFacade:
    """
    Facade for ApiChaosMonkey
    Provides unified interface for all operations.
    """

    def __init__(self):
        self._repository = InMemoryApiChaosMonkeyRepository()
        self._manager = ApiChaosMonkeyManager(self._repository)

    # Add your public methods here
