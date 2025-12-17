"""
Observability API Schemas.
Pydantic models for System Metrics, Health Checks, and Performance Snapshots.
Ensures strict typing and governance for the Observability Domain.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class LegacyResponse(BaseModel, Generic[T]):
    """
    Standard Response Wrapper to maintain backward compatibility.
    Includes 'status', 'timestamp', and optional 'message' fields.
    """
    status: str = Field(..., description="Response status (success/error)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="UTC Timestamp")
    message: str | None = Field(None, description="Optional status message")
    data: T | None = Field(None, description="The actual payload data")


class HealthCheckData(BaseModel):
    """Data for health check response."""
    status: str = "healthy"


class AIOpsMetrics(BaseModel):
    """Pydantic model for AIOps Metrics."""
    anomalies_detected: int
    healing_actions_taken: int
    system_health_score: float
    active_threats: int = 0
    predicted_failures: int = 0


class PerformanceSnapshotModel(BaseModel):
    """Pydantic model for Performance Snapshot."""
    request_count: int | None = Field(None, description="Derived from active_requests + historical if needed")
    error_count: int | None = Field(None, description="Derived error count")

    # Fields matching the dataclass exactly
    timestamp: datetime
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    p999_latency_ms: float
    requests_per_second: float
    error_rate: float
    active_requests: int

    class Config:
        from_attributes = True


class MetricsData(BaseModel):
    """Data payload for the /metrics endpoint."""
    api_performance: PerformanceSnapshotModel
    aiops_health: AIOpsMetrics | dict[str, Any]


class MetricsResponse(BaseModel):
    """
    Specialized response for /metrics to match legacy format:
    {
        "status": "success",
        "timestamp": ...,
        "metrics": { ... }
    }
    """
    status: str = "success"
    timestamp: datetime
    metrics: MetricsData


class EndpointAnalyticsData(BaseModel):
    """Analytics data for a specific endpoint."""
    path: str
    request_count: int
    error_rate: float
    avg_latency: float
    p95_latency: float
    status: str


class AlertModel(BaseModel):
    """Model for a system alert."""
    id: str
    severity: str
    message: str
    timestamp: datetime
    details: dict[str, Any] | None = None


# --- Specific Legacy Formats (Fixing the "Disaster") ---

class AiOpsResponse(BaseModel):
    """
    Legacy format for /metrics/aiops
    Original: {"ok": True, "data": ...}
    """
    ok: bool = True
    data: dict[str, Any]


class SnapshotResponse(BaseModel):
    """
    Legacy format for /performance/snapshot
    Original: {"status": "success", "snapshot": ...}
    """
    status: str = "success"
    snapshot: PerformanceSnapshotModel | dict[str, Any]


class AlertsResponse(BaseModel):
    """
    Legacy format for /alerts
    Original: {"status": "success", "alerts": ...}
    """
    status: str = "success"
    alerts: list[dict[str, Any]]
