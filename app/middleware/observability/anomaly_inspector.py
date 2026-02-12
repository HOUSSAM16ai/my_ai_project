# app/middleware/observability/anomaly_inspector.py
# ======================================================================================
# ==                    ANOMALY INSPECTOR MIDDLEWARE (v∞)                           ==
# ======================================================================================
"""وسيط فحص الشذوذ بلغة واضحة وبلا آثار جانبية غير متوقعة للمبتدئين."""

from dataclasses import dataclass
from time import perf_counter

from app.analysis.anomaly_detector import Anomaly, AnomalyDetector, SeverityLevel
from app.middleware.core.base_middleware import BaseMiddleware
from app.middleware.core.context import RequestContext
from app.middleware.core.result import MiddlewareResult


@dataclass(slots=True)
class AnomalyFinding:
    """نتيجة مفصلة لحالة شاذة مكتشفة أثناء الطلب."""

    path: str
    metric: str
    duration_ms: float
    severity: SeverityLevel
    score: float
    description: str


class AnomalyInspector(BaseMiddleware):
    """وسيط يلتقط بطء الطلبات ويسجّل الحالات الشاذة دون استخدام طباعة عشوائية."""

    name = "AnomalyInspector"
    order = 90  # Execute late to collect all metrics
    _START_TIME_KEY = "anomaly_inspector_start"
    _FINDINGS_KEY = "anomaly_findings"

    def _setup(self) -> None:
        """تهيئة كاشف الشذوذ والمقاييس التراكمية."""
        self.detector: AnomalyDetector = AnomalyDetector()
        self.anomalies_detected: int = 0
        self.inspected_count: int = 0
        self.findings: list[AnomalyFinding] = []

    def process_request(self, ctx: RequestContext) -> MiddlewareResult:
        """يخزن وقت البدء بدقة عالية ويعيد نتيجة نجاح فورية."""
        ctx.add_metadata(self._START_TIME_KEY, perf_counter())
        return MiddlewareResult.success()

    def on_complete(self, ctx: RequestContext, result: MiddlewareResult) -> None:
        """يحسب مدة الطلب ويتحقق من تجاوز العتبات المعرّفة."""
        self.inspected_count += 1

        duration_ms = self._get_request_duration(ctx)
        if duration_ms is None:
            return

        self._check_and_handle_anomaly(ctx, duration_ms)

    def _get_request_duration(self, ctx: RequestContext) -> float | None:
        """يعيد مدة الطلب بالملّي ثانية أو None عند غياب البيانات."""
        start_time = ctx.get_metadata(self._START_TIME_KEY)
        if not isinstance(start_time, int | float):
            return None
        return (perf_counter() - float(start_time)) * 1000

    def _check_and_handle_anomaly(self, ctx: RequestContext, duration_ms: float) -> None:
        """يتحقق من الشذوذ ويسجل النتائج مع إرفاقها بالسياق."""
        metric_name = f"latency_{ctx.path}"
        is_anomaly, anomaly = self.detector.check_value(metric_name, duration_ms)

        if is_anomaly and anomaly:
            self._record_anomaly(ctx, metric_name, duration_ms, anomaly)

    def _record_anomaly(
        self,
        ctx: RequestContext,
        metric_name: str,
        duration_ms: float,
        anomaly: Anomaly,
    ) -> None:
        """يبني نتيجة مهيكلة ويضيفها إلى السجلات والسياق."""
        self.anomalies_detected += 1

        finding = AnomalyFinding(
            path=ctx.path,
            metric=metric_name,
            duration_ms=duration_ms,
            severity=anomaly.severity,
            score=anomaly.score,
            description=anomaly.description,
        )

        self.findings.append(finding)
        self._attach_finding_to_context(ctx, finding)

    def _attach_finding_to_context(self, ctx: RequestContext, finding: AnomalyFinding) -> None:
        """يحافظ على قائمة نتائج الشذوذ في بيانات السياق لتستهلكها الطبقات اللاحقة."""
        existing = ctx.get_metadata(self._FINDINGS_KEY)
        findings: list[AnomalyFinding]
        findings = [*existing] if isinstance(existing, list) else []

        findings.append(finding)
        ctx.add_metadata(self._FINDINGS_KEY, findings)

    def get_statistics(self) -> dict[str, object]:
        """يعيد إحصاءات مهيكلة تتضمن معدل الشذوذ والنتائج الأخيرة."""
        stats = super().get_statistics()
        stats.update(
            {
                "inspected_count": self.inspected_count,
                "anomalies_detected": self.anomalies_detected,
                "anomaly_rate": (
                    self.anomalies_detected / self.inspected_count
                    if self.inspected_count > 0
                    else 0.0
                ),
                "last_finding": self.findings[-1] if self.findings else None,
            }
        )
        return stats
