"""
DataMesh Facade
"""

from .application import DataMeshManager
from .infrastructure import InMemoryDataMeshRepository


class DataMeshFacade:
    """
    Facade for DataMesh
    Provides unified interface for all operations.
    """

    def __init__(self):
        self._repository = InMemoryDataMeshRepository()
        self._manager = DataMeshManager(self._repository)

    # Add your public methods here
