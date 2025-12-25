from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

# ======================================================================================
# ENUMERATIONS
# ======================================================================================


class AnomalyType(Enum):
    """Types of anomalies"""

    LATENCY_SPIKE = "latency_spike"
    ERROR_RATE_INCREASE = "error_rate_increase"
    TRAFFIC_ANOMALY = "traffic_anomaly"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    CAPACITY_LIMIT = "capacity_limit"
    PATTERN_DEVIATION = "pattern_deviation"


class AnomalySeverity(Enum):
    """Anomaly severity levels"""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class HealingAction(Enum):
    """Self-healing actions"""

    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    RESTART_SERVICE = "restart_service"
    INCREASE_TIMEOUT = "increase_timeout"
    ENABLE_CIRCUIT_BREAKER = "enable_circuit_breaker"
    ROUTE_TRAFFIC = "route_traffic"
    CLEAR_CACHE = "clear_cache"
    ADJUST_RATE_LIMIT = "adjust_rate_limit"


class MetricType(Enum):
    """Metric types for telemetry"""

    LATENCY = "latency"
    ERROR_RATE = "error_rate"
    REQUEST_RATE = "request_rate"
    CPU_USAGE = "cpu_usage"
    MEMORY_USAGE = "memory_usage"
    DISK_USAGE = "disk_usage"
    NETWORK_IO = "network_io"


# ======================================================================================
# DATA STRUCTURES
# ======================================================================================


@dataclass
class TelemetryData:
    """Telemetry data point"""

    metric_id: str
    service_name: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    labels: dict[str, str] = field(default_factory=dict)
    unit: str = ""


@dataclass
class AnomalyDetection:
    """Detected anomaly"""

    anomaly_id: str
    service_name: str
    anomaly_type: AnomalyType
    severity: AnomalySeverity
    detected_at: datetime
    metric_value: float
    expected_value: float
    confidence: float  # 0-1
    description: str
    root_causes: list[str] = field(default_factory=list)
    resolved: bool = False
    resolved_at: datetime | None = None


@dataclass
class LoadForecast:
    """Load prediction"""

    forecast_id: str
    service_name: str
    forecast_timestamp: datetime
    predicted_load: float
    confidence_interval: tuple[float, float]
    model_accuracy: float
    generated_at: datetime


@dataclass
class HealingDecision:
    """Self-healing decision"""

    decision_id: str
    anomaly_id: str
    service_name: str
    action: HealingAction
    reason: str
    parameters: dict[str, Any]
    executed_at: datetime | None = None
    success: bool | None = None
    impact: dict[str, Any] = field(default_factory=dict)


@dataclass
class CapacityPlan:
    """Capacity planning recommendation"""

    plan_id: str
    service_name: str
    current_capacity: float
    recommended_capacity: float
    forecast_horizon_hours: int
    expected_peak_load: float
    confidence: float
    created_at: datetime
