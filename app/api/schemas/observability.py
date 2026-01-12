from pydantic import ConfigDict, Field

from app.core.schemas import RobustBaseModel


class HealthComponent(RobustBaseModel):
    """مكون صحة فرعي يوضح حالة نظام محدد."""

    status: str
    details: dict[str, object] | None = None


class HealthResponse(RobustBaseModel):
    """
    نموذج استجابة الصحة العامة.
    """

    status: str = Field(..., description="الحالة العامة للنظام")
    components: dict[str, HealthComponent] | None = Field(None, description="حالة المكونات الفرعية")


class LatencyMetrics(RobustBaseModel):
    """مقاييس زمن الاستجابة للمسارات الساخنة."""

    model_config = ConfigDict(populate_by_name=True)

    p50: float = Field(..., description="الوسيط")
    p95: float = Field(..., description="النسبة المئوية 95")
    p99: float = Field(..., description="النسبة المئوية 99")
    p99_9: float = Field(..., alias="p99.9", description="النسبة المئوية 99.9")
    avg: float = Field(..., description="المتوسط العام")


class TrafficMetrics(RobustBaseModel):
    """إحصاءات حركة المرور على مستوى الخدمة."""

    requests_per_second: float = Field(..., description="عدد الطلبات في الثانية")
    total_requests: int = Field(..., description="إجمالي الطلبات في النافذة الزمنية")


class ErrorMetrics(RobustBaseModel):
    """مقاييس الأخطاء ونسبة فشل الطلبات."""

    error_rate: float = Field(..., description="معدل الأخطاء بالنسبة المئوية")
    error_count: int = Field(..., description="عدد الأخطاء الملاحظة")


class SaturationMetrics(RobustBaseModel):
    """مؤشرات التشبع واستهلاك الموارد."""

    active_requests: int = Field(..., description="عدد الطلبات النشطة")
    queue_depth: int = Field(..., description="عمق طابور التنفيذ")
    active_spans: int | None = Field(None, description="عدد المقاطع التتبعية الفعّالة")
    resource_utilization: float | None = Field(None, description="نسبة استهلاك الموارد")


class GoldenSignalsResponse(RobustBaseModel):
    """
    نموذج الإشارات الذهبية (SRE Golden Signals).
    """

    latency: LatencyMetrics = Field(..., description="مقاييس زمن الاستجابة")
    traffic: TrafficMetrics = Field(..., description="حركة المرور")
    errors: ErrorMetrics = Field(..., description="نسبة الأخطاء")
    saturation: SaturationMetrics = Field(..., description="مؤشرات التشبع")


class AIOpsMetricsResponse(RobustBaseModel):
    """
    نموذج مقاييس الذكاء الاصطناعي للعمليات (AIOps).
    """

    anomaly_score: float = Field(..., description="درجة الشذوذ")
    self_healing_events: int = Field(0, description="عدد أحداث المعالجة الذاتية")
    predictions: dict[str, object] | None = Field(None, description="توقعات مستقبلية")


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
