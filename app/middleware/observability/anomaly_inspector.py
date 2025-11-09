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

    def on_complete(self, ctx: RequestContext, result: MiddlewareResult):
        """
        Inspect for anomalies

        Args:
            ctx: Request context
            result: Middleware result
        """
        self.inspected_count += 1

        # Get duration
        start_time = ctx.get_metadata("anomaly_inspector_start")
        if not start_time:
            return

        duration_ms = (time.time() - start_time) * 1000

        # Check for latency anomalies
        metric_name = f"latency_{ctx.path}"
        is_anomaly, anomaly = self.detector.check_value(metric_name, duration_ms)

        if is_anomaly and anomaly:
            self.anomalies_detected += 1

            # Store anomaly info in context
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

            # Log anomaly (would integrate with logging system)
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
