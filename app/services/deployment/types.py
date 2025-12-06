# app/services/deployment/types.py
"""
Data Structures and Enums for the Deployment Orchestration System.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any, Optional


class DeploymentStrategy(Enum):
    """استراتيجيات النشر"""

    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    ROLLING = "rolling"
    RECREATE = "recreate"
    A_B_TESTING = "ab_testing"
    SHADOW = "shadow"


class DeploymentPhase(Enum):
    """مراحل النشر"""

    PREPARING = "preparing"
    DEPLOYING = "deploying"
    TESTING = "testing"
    TRAFFIC_SHIFTING = "traffic_shifting"
    MONITORING = "monitoring"
    COMPLETED = "completed"
    ROLLING_BACK = "rolling_back"
    FAILED = "failed"


class HealthCheckType(Enum):
    """أنواع فحوصات الصحة"""

    LIVENESS = "liveness"  # هل الخدمة حية؟
    READINESS = "readiness"  # هل الخدمة جاهزة لاستقبال الطلبات؟
    STARTUP = "startup"  # هل اكتمل التشغيل؟


class CircuitState(Enum):
    """حالات قاطع الدائرة"""

    CLOSED = "closed"  # كل شيء يعمل
    OPEN = "open"  # فشل متكرر - إيقاف الطلبات
    HALF_OPEN = "half_open"  # محاولة تجريبية


class RollbackTrigger(Enum):
    """مُحفزات التراجع التلقائي"""

    ERROR_RATE_HIGH = "error_rate_high"
    LATENCY_HIGH = "latency_high"
    HEALTH_CHECK_FAILED = "health_check_failed"
    MANUAL = "manual"
    ANOMALY_DETECTED = "anomaly_detected"


@dataclass
class ServiceVersion:
    """نسخة الخدمة"""

    version_id: str
    service_name: str
    version_number: str
    image_tag: str
    replicas: int
    health_endpoint: str
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class HealthCheckConfig:
    """إعدادات فحص الصحة"""

    check_type: HealthCheckType
    path: str
    interval_seconds: int = 10
    timeout_seconds: int = 5
    success_threshold: int = 1
    failure_threshold: int = 3
    initial_delay_seconds: int = 5


@dataclass
class DeploymentConfig:
    """إعدادات النشر"""

    strategy: DeploymentStrategy
    service_name: str
    new_version: ServiceVersion
    old_version: Optional[ServiceVersion] = None
    auto_rollback: bool = True
    health_checks: list[HealthCheckConfig] = field(default_factory=list)

    # إعدادات خاصة بالاستراتيجيات
    canary_percentage_steps: list[int] = field(default_factory=lambda: [10, 50, 100])
    canary_interval_seconds: int = 60
    max_surge: int = 1  # للتحديث المتدحرج
    max_unavailable: int = 0  # للتحديث المتدحرج
    traffic_shifting_enabled: bool = True


@dataclass
class TrafficSplit:
    """تقسيم الترافيك"""

    new_version_percentage: int
    old_version_percentage: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class DeploymentStatus:
    """حالة النشر الحالية"""

    deployment_id: str
    config: DeploymentConfig
    phase: DeploymentPhase
    start_time: datetime = field(default_factory=lambda: datetime.now(UTC))
    end_time: Optional[datetime] = None
    traffic_split: Optional[TrafficSplit] = None
    events: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)


@dataclass
class CircuitBreakerStatus:
    """حالة قاطع الدائرة"""

    service_name: str
    state: CircuitState
    last_failure_time: Optional[datetime] = None
    total_failures: int = 0
    consecutive_failures: int = 0
    last_success_time: Optional[datetime] = None
    reset_timeout_seconds: int = 60
