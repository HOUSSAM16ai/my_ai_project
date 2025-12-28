from typing import Any

from pydantic import Field

from app.core.schemas import RobustBaseModel


class HealthComponent(RobustBaseModel):
    status: str
    details: dict[str, Any] | None = None


class HealthResponse(RobustBaseModel):
    """
    نموذج استجابة الصحة العامة.
    """
    status: str = Field(..., description="الحالة العامة للنظام")
    components: dict[str, HealthComponent] | None = Field(None, description="حالة المكونات الفرعية")


class GoldenSignalsResponse(RobustBaseModel):
    """
    نموذج الإشارات الذهبية (SRE Golden Signals).
    """
    latency: float = Field(..., description="زمن الاستجابة (ms)")
    traffic: float = Field(..., description="معدل الطلبات (req/s)")
    errors: float = Field(..., description="معدل الأخطاء (%)")
    saturation: float = Field(..., description="درجة التشبع (%)")


class AIOpsMetricsResponse(RobustBaseModel):
    """
    نموذج مقاييس الذكاء الاصطناعي للعمليات (AIOps).
    """
    anomaly_score: float = Field(..., description="درجة الشذوذ")
    self_healing_events: int = Field(0, description="عدد أحداث المعالجة الذاتية")
    predictions: dict[str, Any] | None = Field(None, description="توقعات مستقبلية")


class GitOpsMetricsResponse(RobustBaseModel):
    """
    نموذج مقاييس GitOps.
    """
    status: str = Field(..., description="حالة المزامنة")
    sync_rate: float = Field(..., description="معدل المزامنة (%)")
    last_sync: str | None = Field(None, description="توقيت آخر مزامنة")


class PerformanceSnapshotResponse(RobustBaseModel):
    """
    نموذج لقطة الأداء.
    """
    cpu_usage: float = Field(..., description="استهلاك المعالج (%)")
    memory_usage: float = Field(..., description="استهلاك الذاكرة (%)")
    active_requests: int = Field(..., description="عدد الطلبات النشطة")


class EndpointAnalyticsResponse(RobustBaseModel):
    """
    نموذج تحليلات نقطة النهاية.
    """
    path: str = Field(..., description="مسار نقطة النهاية")
    avg_latency: float = Field(..., description="متوسط زمن الاستجابة")
    p95_latency: float = Field(..., description="P95 Latency")
    error_count: int = Field(0, description="عدد الأخطاء")
    total_calls: int = Field(0, description="إجمالي الاستدعاءات")


class AlertResponse(RobustBaseModel):
    """
    نموذج التنبيه.
    """
    id: str
    severity: str
    message: str
    timestamp: str
    status: str
