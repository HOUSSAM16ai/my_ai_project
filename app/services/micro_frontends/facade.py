"""
MicroFrontends Facade
"""

from .application import MicroFrontendsManager
from .infrastructure import InMemoryMicroFrontendsRepository


class MicroFrontendsFacade:
    """
    Facade for MicroFrontends
    Provides unified interface for all operations.
    """

    def __init__(self):
        self._repository = InMemoryMicroFrontendsRepository()
        self._manager = MicroFrontendsManager(self._repository)

    # Add your public methods here
