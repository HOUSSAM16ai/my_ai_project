"""
Platform Boundary Service
------------------------
Encapsulates the 'Intelligent Platform' aggregation logic, enforcing a strict boundary
between the HTTP API layer (Routers) and the underlying domain services (Data Mesh, AIOps, etc.).

Architecture:
- Acts as a Facade / Aggregator for the "Superhuman" Platform Services.
- Handles DTO -> Domain mapping (Adapter pattern).
- Provides a unified entry point for platform-level operations.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from app.core.di import get_logger
from app.services.aiops_self_healing_service import (
    AIOpsService,
    MetricType,
    TelemetryData,
    get_aiops_service,
)
from app.services.api_observability_service import (
    APIObservabilityService,
    PerformanceSnapshot,
    get_observability_service,
)
from app.services.data_mesh_service import (
    DataContract,
    DataDomainType,
    DataMeshService,
    DataProductStatus,
    SchemaCompatibility,
    get_data_mesh_service,
)
from app.services.edge_multicloud_service import EdgeMultiCloudService, get_edge_multicloud_service
from app.services.gitops_policy_service import GitOpsService, get_gitops_service
from app.services.sre_error_budget_service import SREErrorBudgetService, get_sre_service
from app.services.workflow_orchestration_service import (
    WorkflowOrchestrationService,
    get_workflow_orchestration_service,
)

logger = get_logger(__name__)


class PlatformBoundaryService:
    """
    The Boundary Service for the Intelligent Platform.
    Decouples the API Router from the complex aggregation logic of the underlying subsystems.
    """

    def __init__(
        self,
        data_mesh: DataMeshService,
        aiops: AIOpsService,
        gitops: GitOpsService,
        workflows: WorkflowOrchestrationService,
        edge: EdgeMultiCloudService,
        sre: SREErrorBudgetService,
        observability: APIObservabilityService,
    ):
        self.data_mesh = data_mesh
        self.aiops = aiops
        self.gitops = gitops
        self.workflows = workflows
        self.edge = edge
        self.sre = sre
        self.observability = observability

    async def get_platform_overview(self) -> dict[str, Any]:
        """
        Aggregates metrics from all 'Superhuman' subsystems into a unified dashboard view.
        """
        try:
            return {
                "data_mesh": self.data_mesh.get_mesh_metrics(),
                "aiops": self.aiops.get_aiops_metrics(),
                "gitops": self.gitops.get_gitops_metrics(),
                "workflows": self.workflows.get_metrics(),
                "edge_multicloud": self.edge.get_metrics(),
                "sre": self.sre.get_sre_metrics(),
                # New: API Observability Metrics
                "observability": {
                    "snapshot": self.observability.get_performance_snapshot(),
                    "compliance": self.observability.get_sla_compliance(),
                },
            }
        except Exception as e:
            logger.error(f"Error gathering platform overview: {e}", exc_info=True)
            raise

    # --- API Observability Methods ---

    async def get_performance_snapshot(self) -> PerformanceSnapshot:
        """
        Get current API performance snapshot including P99 latency.
        Delegates to APIObservabilityService.
        """
        return self.observability.get_performance_snapshot()

    async def get_endpoint_analytics(self, path: str) -> dict[str, Any]:
        """
        Get detailed analytics for a specific endpoint.
        Delegates to APIObservabilityService.
        """
        return self.observability.get_endpoint_analytics(path)

    async def get_system_alerts(self, severity: str | None = None) -> list[dict[str, Any]]:
        """
        Get active system alerts (Anomalies, SLA Violations).
        Delegates to APIObservabilityService.
        """
        return self.observability.get_all_alerts(severity)

    # --- Data Mesh Methods ---

    async def create_data_contract(
        self,
        domain: DataDomainType,
        name: str,
        description: str,
        schema_version: str,
        schema_definition: dict[str, Any],
        compatibility_mode: SchemaCompatibility = SchemaCompatibility.BACKWARD,
        owners: list[str] | None = None,
        consumers: list[str] | None = None,
        sla_guarantees: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """
        Orchestrates the creation of a Data Contract.
        Handles the mapping from API primitives to the DataContract domain entity.
        """
        contract = DataContract(
            contract_id=str(uuid.uuid4()),
            domain=domain,
            name=name,
            description=description,
            schema_version=schema_version,
            schema_definition=schema_definition,
            compatibility_mode=compatibility_mode,
            owners=owners or [],
            consumers=consumers or [],
            sla_guarantees=sla_guarantees or {},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            status=DataProductStatus.ACTIVE,
            metadata=metadata or {},
        )

        logger.info(f"Creating Data Contract via Boundary: {name} ({domain})")
        return self.data_mesh.create_data_contract(contract)

    # --- Telemetry Methods ---

    async def collect_telemetry(
        self,
        service_name: str,
        metric_type: MetricType,
        value: float,
        labels: dict[str, str] | None = None,
        unit: str = "",
        timestamp: datetime | None = None,
    ) -> bool:
        """
        Orchestrates the collection of telemetry data.
        Handles mapping to TelemetryData domain entity.
        """
        telemetry = TelemetryData(
            metric_id=str(uuid.uuid4()),
            service_name=service_name,
            metric_type=metric_type,
            value=value,
            timestamp=timestamp or datetime.now(UTC),
            labels=labels or {},
            unit=unit,
        )

        self.aiops.collect_telemetry(telemetry)
        return True


# Singleton Factory for Dependency Injection
_platform_boundary_instance: PlatformBoundaryService | None = None


def get_platform_boundary_service() -> PlatformBoundaryService:
    """
    Dependency Injection factory for the PlatformBoundaryService.
    Lazy loads the singleton instance with all dependencies resolved.
    """
    global _platform_boundary_instance

    if _platform_boundary_instance is None:
        _platform_boundary_instance = PlatformBoundaryService(
            data_mesh=get_data_mesh_service(),
            aiops=get_aiops_service(),
            gitops=get_gitops_service(),
            workflows=get_workflow_orchestration_service(),
            edge=get_edge_multicloud_service(),
            sre=get_sre_service(),
            observability=get_observability_service(),
        )

    return _platform_boundary_instance
