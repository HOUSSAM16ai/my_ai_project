"""
AuthBoundary Facade
"""

from .application import AuthBoundaryManager
from .infrastructure import InMemoryAuthBoundaryRepository


class AuthBoundaryFacade:
    """
    Facade for AuthBoundary
    Provides unified interface for all operations.
    """

    def __init__(self):
        self._repository = InMemoryAuthBoundaryRepository()
        self._manager = AuthBoundaryManager(self._repository)

    # Add your public methods here
