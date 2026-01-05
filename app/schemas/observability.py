"""نماذج مراقبة النظام بوضوح عربي وتجنّب الأنواع العامة لتسهيل الصيانة."""

from __future__ import annotations

from datetime import datetime
from typing import TypeVar

from pydantic import BaseModel, Field

from app.protocols.http_client import JsonValue

T = TypeVar("T")


class LegacyResponse[T](BaseModel):
    """غلاف استجابة قياسي يحافظ على التوافق العكسي مع الحقول الأساسية."""

    status: str = Field(..., description="حالة الاستجابة (نجاح/فشل)")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="تاريخ ووقت UTC")
    message: str | None = Field(None, description="رسالة حالة اختيارية")
    data: T | None = Field(None, description="الحمولة الفعلية للرد")


class HealthCheckData(BaseModel):
    """بيانات فحص الصحة الافتراضية للمنظومة."""

    status: str = "healthy"


class AIOpsMetrics(BaseModel):
    """تمثيل مقاييس AIOps بأرقام واضحة للمراقبة."""

    anomalies_detected: int
    healing_actions_taken: int
    system_health_score: float
    active_threats: int = 0
    predicted_failures: int = 0


class PerformanceSnapshotModel(BaseModel):
    """لقطة أداء مفصلة للمؤشرات الزمنية وحمل الطلبات."""

    request_count: int | None = Field(None, description="عدد الطلبات المشتق عند الحاجة")
    error_count: int | None = Field(None, description="عدد الأخطاء المشتق")

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
    """حمولة بيانات مسار /metrics مع دعم كائنات AIOps أو تمثيلها كقاموس."""

    api_performance: PerformanceSnapshotModel
    aiops_health: AIOpsMetrics | dict[str, JsonValue]


class MetricsResponse(BaseModel):
    """استجابة مهيكلة لمسار /metrics تحافظ على التنسيق القديم."""

    status: str = "success"
    timestamp: datetime
    metrics: MetricsData


class EndpointAnalyticsData(BaseModel):
    """بيانات تحليلات نقطة نهاية محددة لتمكين القراءة السريعة."""

    path: str
    request_count: int
    error_rate: float
    avg_latency: float
    p95_latency: float
    status: str


class AlertModel(BaseModel):
    """نموذج إنذار النظام مع تفاصيل اختيارية قابلة للتسلسل."""

    id: str
    severity: str
    message: str
    timestamp: datetime
    details: dict[str, JsonValue] | None = None


class AiOpsResponse(BaseModel):
    """تنسيق قديم لمسار /metrics/aiops يحافظ على مفاتيح ok و data."""

    ok: bool = True
    data: dict[str, JsonValue]


class SnapshotResponse(BaseModel):
    """تنسيق قديم لمسار /performance/snapshot مع حمولة لقطة الأداء."""

    status: str = "success"
    snapshot: PerformanceSnapshotModel | dict[str, JsonValue]


class AlertsResponse(BaseModel):
    """تنسيق قديم لمسار /alerts يحوي قائمة إنذارات قابلة للتحليل."""

    status: str = "success"
    alerts: list[dict[str, JsonValue]]
