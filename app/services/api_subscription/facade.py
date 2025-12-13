"""
ApiSubscription Facade
"""

from .application import ApiSubscriptionManager
from .infrastructure import InMemoryApiSubscriptionRepository


class ApiSubscriptionFacade:
    """
    Facade for ApiSubscription
    Provides unified interface for all operations.
    """

    def __init__(self):
        self._repository = InMemoryApiSubscriptionRepository()
        self._manager = ApiSubscriptionManager(self._repository)

    # Add your public methods here
