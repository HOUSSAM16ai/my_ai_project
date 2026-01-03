# app/middleware/observability/anomaly_inspector.py
# ======================================================================================
# ==                    ANOMALY INSPECTOR MIDDLEWARE (v∞)                           ==
# ======================================================================================
"""
مفتش الحالات الشاذة - Anomaly Inspector

ML-powered anomaly detection middleware that identifies unusual
patterns in request behavior and performance.
"""

import time

from app.analysis.anomaly_detector import AnomalyDetector
from app.middleware.core.base_middleware import BaseMiddleware
from app.middleware.core.context import RequestContext
from app.middleware.core.result import MiddlewareResult

class AnomalyInspector(BaseMiddleware):
    """
    Anomaly Inspector Middleware

    Features:
    - Statistical anomaly detection
    - ML-based pattern recognition
    - Real-time alerting
    - Adaptive thresholds
    """

    name = "AnomalyInspector"
    order = 90  # Execute late to collect all metrics

    def _setup(self):
        """Initialize anomaly detector"""
        self.detector = AnomalyDetector()
        self.anomalies_detected = 0
        self.inspected_count = 0

    def process_request(self, ctx: RequestContext) -> MiddlewareResult:
        """
        Start anomaly inspection

        Args:
            ctx: Request context

        Returns:
            Always succeeds
        """
        ctx.add_metadata("anomaly_inspector_start", time.time())
        return MiddlewareResult.success()

    def on_complete(self, ctx: RequestContext, result: MiddlewareResult) -> None:
        """Inspect for anomalies - KISS principle applied"""
        self.inspected_count += 1

        duration_ms = self._get_request_duration(ctx)
        if duration_ms is None:
            return

        self._check_and_handle_anomaly(ctx, duration_ms)

    def _get_request_duration(self, ctx: RequestContext) -> float:
        """Calculate request duration in milliseconds"""
        start_time = ctx.get_metadata("anomaly_inspector_start")
        if not start_time:
            return None
        return (time.time() - start_time) * 1000

    def _check_and_handle_anomaly(self, ctx: RequestContext, duration_ms: float) -> None:
        """Check for anomalies and handle if detected"""
        metric_name = f"latency_{ctx.path}"
        is_anomaly, anomaly = self.detector.check_value(metric_name, duration_ms)

        if is_anomaly and anomaly:
            self._record_anomaly(ctx, metric_name, duration_ms, anomaly)
            self._log_critical_anomaly(ctx, duration_ms, anomaly)

    def _record_anomaly(self, ctx: RequestContext, metric_name: str, 
                        duration_ms: float, anomaly) -> None:
        """Record anomaly in context"""
        self.anomalies_detected += 1
        ctx.add_metadata(
            "anomaly_detected",
            {
                "metric": metric_name,
                "value": duration_ms,
                "score": anomaly.score,
                "severity": anomaly.severity.value,
                "description": anomaly.description,
            },
        )

    def _log_critical_anomaly(self, ctx: RequestContext, duration_ms: float, anomaly) -> None:
        """Log high/critical severity anomalies"""
        if anomaly.severity.value in ["high", "critical"]:
            print(
                f"⚠️  Anomaly detected: {ctx.path} - "
                f"latency {duration_ms:.2f}ms (score: {anomaly.score:.2f})"
            )

    def get_statistics(self) -> dict:
        """Return anomaly inspector statistics"""
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
            }
        )
        return stats
