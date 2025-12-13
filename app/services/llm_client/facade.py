"""
LlmClient Facade
"""

from .application import LlmClientManager
from .infrastructure import InMemoryLlmClientRepository


class LlmClientFacade:
    """
    Facade for LlmClient
    Provides unified interface for all operations.
    """

    def __init__(self):
        self._repository = InMemoryLlmClientRepository()
        self._manager = LlmClientManager(self._repository)

    # Add your public methods here
