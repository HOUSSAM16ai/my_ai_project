from __future__ import annotations

import logging
import threading

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

# Export Domain Models for external consumption
__all__ = [
    "BoundedContext",
    "DataContract",
    "DataDomainType",
    "DataMeshService",
    "DataProduct",
    "DataProductStatus",
    "DataQualityMetrics",
    "GovernanceLevel",
    "GovernancePolicy",
    "SchemaCompatibility",
    "SchemaEvolution",
    "get_data_mesh_service",
]


class DataMeshService:
    """
    Facade for the Superhuman Data Mesh Service (v2.0 - Hexagonal Edition).
    Delegates all logic to the Application Manager while maintaining the original interface.
    """

    def __init__(self):
        self._manager = DataMeshManager()
        logging.getLogger(__name__).info("Data Mesh Service Facade initialized")

    # Delegate all properties and methods to the manager
    # Note: We implement explicit delegation rather than __getattr__ to maintain
    # static analysis support and IDE completion.

    @property
    def bounded_contexts(self):
        return self._manager.bounded_contexts

    @property
    def data_contracts(self):
        return self._manager.data_contracts

    @property
    def data_products(self):
        return self._manager.data_products

    @property
    def governance_policies(self):
        return self._manager.governance_policies

    @property
    def quality_metrics(self):
        return self._manager.quality_metrics

    @property
    def schema_evolutions(self):
        return self._manager.schema_evolutions

    @property
    def event_streams(self):
        return self._manager.event_streams

    def register_bounded_context(self, context: BoundedContext) -> bool:
        return self._manager.register_bounded_context(context)

    def get_bounded_context(self, context_id: str) -> BoundedContext | None:
        return self._manager.get_bounded_context(context_id)

    def create_data_contract(self, contract: DataContract) -> bool:
        return self._manager.create_data_contract(contract)

    def evolve_contract_schema(
        self, contract_id: str, new_schema: dict, new_version: str, changes: list[dict]
    ) -> SchemaEvolution | None:
        return self._manager.evolve_contract_schema(
            contract_id, new_schema, new_version, changes
        )

    def _validate_schema_compatibility(self, contract: DataContract) -> bool:
        return self._manager._validate_schema_compatibility(contract)

    def _detect_schema_compatibility(
        self, old_schema: dict, new_schema: dict, changes: list[dict]
    ) -> SchemaCompatibility:
        return self._manager._detect_schema_compatibility(old_schema, new_schema, changes)

    def register_data_product(self, product: DataProduct) -> bool:
        return self._manager.register_data_product(product)

    def get_data_products_by_domain(self, domain: DataDomainType) -> list[DataProduct]:
        return self._manager.get_data_products_by_domain(domain)

    def add_governance_policy(self, policy: GovernancePolicy) -> bool:
        return self._manager.add_governance_policy(policy)

    def _check_governance_compliance(self, contract: DataContract) -> bool:
        return self._manager._check_governance_compliance(contract)

    def _evaluate_governance_rule(self, contract: DataContract, rule: dict) -> bool:
        return self._manager._evaluate_governance_rule(contract, rule)

    def record_quality_metrics(self, metrics: DataQualityMetrics):
        return self._manager.record_quality_metrics(metrics)

    def _check_quality_thresholds(self, metrics: DataQualityMetrics):
        return self._manager._check_quality_thresholds(metrics)

    def _trigger_governance_action(self, policy: GovernancePolicy, reason: str):
        return self._manager._trigger_governance_action(policy, reason)

    def get_quality_summary(self, product_id: str) -> dict | None:
        return self._manager.get_quality_summary(product_id)

    def _publish_event(self, event_type: str, payload: dict):
        return self._manager._publish_event(event_type, payload)

    def subscribe_to_events(self, event_type: str, callback) -> str:
        return self._manager.subscribe_to_events(event_type, callback)

    def get_event_stream(self, event_type: str, limit: int = 100) -> list[dict]:
        return self._manager.get_event_stream(event_type, limit)

    def get_mesh_metrics(self) -> dict:
        return self._manager.get_mesh_metrics()


# Singleton Management
_data_mesh_instance: DataMeshService | None = None
_mesh_lock = threading.Lock()


def get_data_mesh_service() -> DataMeshService:
    """Get singleton data mesh service instance"""
    global _data_mesh_instance

    if _data_mesh_instance is None:
        with _mesh_lock:
            if _data_mesh_instance is None:
                _data_mesh_instance = DataMeshService()

    return _data_mesh_instance
