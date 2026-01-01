from __future__ import annotations

import logging

from app.services.observability.aiops.service import AIOpsService, get_aiops_service
from app.telemetry.unified_observability import (
    UnifiedObservabilityService,
    get_unified_observability,
)

class ObservabilityBoundaryService:
    """
    Unified Boundary Service for Observability.
    Aggregates AIOps, Telemetry, and Monitoring signals into a single clean interface.
    Follows Separation of Concerns by isolating the Router from underlying implementations.
    """

    def __init__(
        self,
        aiops_service: AIOpsService | None = None,
        telemetry_service: UnifiedObservabilityService | None = None,
    ):
        self.aiops = aiops_service or get_aiops_service()
        self.telemetry = telemetry_service or get_unified_observability()
        self.logger = logging.getLogger(__name__)

    async def get_system_health(self) -> dict[str, Any]:
        """
        Aggregates system health from multiple sources.
        """
        return {
            "status": "ok",
            "system": "superhuman",
            "timestamp": self.telemetry.get_golden_signals()["timestamp"],
        }

    async def get_golden_signals(self) -> dict[str, Any]:
        """
        Retrieves SRE Golden Signals (Latency, Traffic, Errors, Saturation).
        """
        return self.telemetry.get_golden_signals()

    async def get_aiops_metrics(self) -> dict[str, Any]:
        """
        Retrieves AIOps specific metrics (Anomalies, Healing Decisions).
        """
        return self.aiops.get_aiops_metrics()

    async def get_performance_snapshot(self) -> dict[str, Any]:
        """
        Get a comprehensive snapshot of performance statistics.
        """
        return self.telemetry.get_statistics()

    async def get_endpoint_analytics(self, path: str) -> list[dict[str, Any]]:
        """
        Analyzes traces for a specific endpoint path.
        """
        return self.telemetry.find_traces_by_criteria(operation_name=path)

    async def get_active_alerts(self) -> list[Any]:
        """
        Retrieves active anomaly alerts from the system.
        """
        # Convert deque to list
        return list(self.telemetry.anomaly_alerts)
