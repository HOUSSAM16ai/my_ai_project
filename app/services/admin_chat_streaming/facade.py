"""
AdminChatStreaming Facade
"""

from .application import AdminChatStreamingManager
from .infrastructure import InMemoryAdminChatStreamingRepository


class AdminChatStreamingFacade:
    """
    Facade for AdminChatStreaming
    Provides unified interface for all operations.
    """

    def __init__(self):
        self._repository = InMemoryAdminChatStreamingRepository()
        self._manager = AdminChatStreamingManager(self._repository)

    # Add your public methods here
