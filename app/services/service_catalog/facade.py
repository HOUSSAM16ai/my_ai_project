"""
ServiceCatalog Facade
"""

from .application import ServiceCatalogManager
from .infrastructure import InMemoryServiceCatalogRepository


class ServiceCatalogFacade:
    """
    Facade for ServiceCatalog
    Provides unified interface for all operations.
    """

    def __init__(self):
        self._repository = InMemoryServiceCatalogRepository()
        self._manager = ServiceCatalogManager(self._repository)

    # Add your public methods here
