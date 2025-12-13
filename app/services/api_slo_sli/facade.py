"""
ApiSloSli Facade
"""

from .application import ApiSloSliManager
from .infrastructure import InMemoryApiSloSliRepository


class ApiSloSliFacade:
    """
    Facade for ApiSloSli
    Provides unified interface for all operations.
    """

    def __init__(self):
        self._repository = InMemoryApiSloSliRepository()
        self._manager = ApiSloSliManager(self._repository)

    # Add your public methods here
