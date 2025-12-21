# app/services/adaptive/domain/models.py
"""
Adaptive Microservices Domain Models
=====================================
Pure business entities and enumerations for AI-driven adaptive microservices.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class ServiceHealth(Enum):
    """حالة صحة الخدمة"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    RECOVERING = "recovering"


class ScalingDirection(Enum):
    """اتجاه التوسع"""

    UP = "scale_up"
    DOWN = "scale_down"
    STABLE = "stable"


@dataclass
class ServiceMetrics:
    """مقاييس الخدمة في الوقت الفعلي"""

    service_name: str
    timestamp: datetime
    cpu_usage: float  # 0-100
    memory_usage: float  # 0-100
    request_rate: float  # requests per second
    error_rate: float  # 0-100
    latency_p50: float  # milliseconds
    latency_p95: float  # milliseconds
    latency_p99: float  # milliseconds
    active_connections: int
    queue_depth: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "service_name": self.service_name,
            "timestamp": self.timestamp.isoformat(),
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "request_rate": self.request_rate,
            "error_rate": self.error_rate,
            "latency_p50": self.latency_p50,
            "latency_p95": self.latency_p95,
            "latency_p99": self.latency_p99,
            "active_connections": self.active_connections,
            "queue_depth": self.queue_depth,
        }


@dataclass
class ScalingDecision:
    """قرار التوسع الذكي"""

    service_name: str
    direction: ScalingDirection
    current_instances: int
    target_instances: int
    confidence: float  # 0-1
    reason: str
    predicted_impact: dict[str, float]
    timestamp: datetime


@dataclass
class ServiceInstance:
    """نموذج خدمة مصغرة"""

    instance_id: str
    service_name: str
    status: ServiceHealth
    cpu_limit: float = 80.0
    memory_limit: float = 80.0
    created_at: datetime = field(default_factory=datetime.now)
    last_health_check: datetime | None = None
    metrics_history: deque = field(default_factory=lambda: deque(maxlen=100))

    def is_healthy(self) -> bool:
        return self.status == ServiceHealth.HEALTHY
