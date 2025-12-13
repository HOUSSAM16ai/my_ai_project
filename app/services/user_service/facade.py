"""
UserService Facade
"""

from .application import UserServiceManager
from .infrastructure import InMemoryUserServiceRepository


class UserServiceFacade:
    """
    Facade for UserService
    Provides unified interface for all operations.
    """

    def __init__(self):
        self._repository = InMemoryUserServiceRepository()
        self._manager = UserServiceManager(self._repository)

    # Add your public methods here
