"""
DistributedResilience Facade
"""

from .application import DistributedResilienceManager
from .infrastructure import InMemoryDistributedResilienceRepository


class DistributedResilienceFacade:
    """
    Facade for DistributedResilience
    Provides unified interface for all operations.
    """

    def __init__(self):
        self._repository = InMemoryDistributedResilienceRepository()
        self._manager = DistributedResilienceManager(self._repository)

    # Add your public methods here
