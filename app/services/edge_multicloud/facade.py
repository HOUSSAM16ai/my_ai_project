"""
EdgeMulticloud Facade
"""

from .application import EdgeMulticloudManager
from .infrastructure import InMemoryEdgeMulticloudRepository


class EdgeMulticloudFacade:
    """
    Facade for EdgeMulticloud
    Provides unified interface for all operations.
    """

    def __init__(self):
        self._repository = InMemoryEdgeMulticloudRepository()
        self._manager = EdgeMulticloudManager(self._repository)

    # Add your public methods here
