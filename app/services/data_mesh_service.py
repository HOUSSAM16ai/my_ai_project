# app/services/data_mesh_service.py
"""
Backward compatibility module for DataMeshService.
This module re-exports the components from the new 'app.services.data_mesh' package.
"""

from app.services.data_mesh import (
    BoundedContext,
    DataContract,
    DataDomainType,
    DataMeshService,
    DataProduct,
    DataProductStatus,
    DataQualityMetrics,
    GovernanceLevel,
    GovernancePolicy,
    SchemaCompatibility,
    SchemaEvolution,
    get_data_mesh_service,
)

__all__ = [
    "DataMeshService",
    "get_data_mesh_service",
    "DataDomainType",
    "DataProductStatus",
    "SchemaCompatibility",
    "GovernanceLevel",
    "DataContract",
    "DataProduct",
    "BoundedContext",
    "GovernancePolicy",
    "DataQualityMetrics",
    "SchemaEvolution",
]
