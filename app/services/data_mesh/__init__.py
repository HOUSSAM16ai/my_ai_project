"""
Data Mesh Service - SOLID Principles Applied
============================================

Simplified to use direct manager access instead of unnecessary facade layer.
This follows KISS (Keep It Simple) and removes abstraction that adds no value.
"""

from app.services.data_mesh.application.mesh_manager import DataMeshManager
from app.services.data_mesh.domain.models import (
    BoundedContext,
    DataContract,
    DataDomainType,
    DataProduct,
    DataProductStatus,
    DataQualityMetrics,
    GovernanceLevel,
    GovernancePolicy,
    SchemaCompatibility,
    SchemaEvolution,
)

# Singleton instance
_manager_instance: DataMeshManager | None = None

def get_data_mesh_service() -> DataMeshManager:
    """
    Get singleton Data Mesh Manager instance.

    Note: Renamed from get_data_mesh_service for backward compatibility,
    but now returns DataMeshManager directly (KISS principle).
    """
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = DataMeshManager()
    return _manager_instance

__all__ = [
    "BoundedContext",
    "DataContract",
    "DataDomainType",
    "DataMeshManager",
    "DataProduct",
    "DataProductStatus",
    "DataQualityMetrics",
    "GovernanceLevel",
    "GovernancePolicy",
    "SchemaCompatibility",
    "SchemaEvolution",
    "get_data_mesh_service",
]
