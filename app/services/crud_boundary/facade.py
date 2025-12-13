"""
CrudBoundary Facade
"""

from .application import CrudBoundaryManager
from .infrastructure import InMemoryCrudBoundaryRepository


class CrudBoundaryFacade:
    """
    Facade for CrudBoundary
    Provides unified interface for all operations.
    """

    def __init__(self):
        self._repository = InMemoryCrudBoundaryRepository()
        self._manager = CrudBoundaryManager(self._repository)

    # Add your public methods here
