# app/middleware/security/ai_threat_middleware.py
# ======================================================================================
# ==                    AI THREAT DETECTION MIDDLEWARE (v∞)                         ==
# ======================================================================================
"""
وسيط كشف التهديدات بالذكاء الاصطناعي - AI Threat Detection Middleware

Adapter for AI-powered threat detection using the new middleware architecture.
Uses machine learning to identify behavioral anomalies and threats.
"""

from app.middleware.core.base_middleware import BaseMiddleware
from app.middleware.core.context import RequestContext
from app.middleware.core.result import MiddlewareResult
from app.security.threat_detector import AIThreatDetector

class AIThreatMiddleware(BaseMiddleware):
    """
    AI-Powered Threat Detection Middleware

    Features:
    - Behavioral analysis
    - Anomaly detection
    - Pattern recognition
    - Risk scoring
    """

    name = "AIThreat"
    order = 20  # Execute after WAF, before rate limiting

    def _setup(self):
        """Initialize AI threat detector"""
        self.ai_detector = AIThreatDetector()
        self.threats_detected = 0
        self.analyzed_count = 0
        self.critical_blocks = 0

    def process_request(self, ctx: RequestContext) -> MiddlewareResult:
        """Analyze request for AI-detected threats - KISS principle applied"""
        self.analyzed_count += 1

        # Skip AI analysis for health checks
        if self._is_health_check(ctx.path):
            return MiddlewareResult.success()

        try:
            threat_score, detection = self._analyze_threat(ctx)
            ctx.add_metadata("threat_score", threat_score)

            if detection:
                return self._handle_threat(detection, threat_score, ctx)

            return MiddlewareResult.success()

        except Exception as e:
            return self._handle_error(e)

    def _is_health_check(self, path: str) -> bool:
        """Check if path is a health check endpoint"""
        return path in ["/health", "/api/health", "/ping"]

    def _analyze_threat(self, ctx: RequestContext) -> tuple:
        """Analyze request for threats using AI detector"""
        return self.ai_detector.analyze_request(
            ctx._raw_request,
            ctx.ip_address,
        )

    def _handle_threat(self, detection, threat_score: float, ctx: RequestContext) -> MiddlewareResult:
        """Handle detected threat based on severity"""
        self.threats_detected += 1

        if detection.severity == "critical":
            return self._block_critical_threat(detection, threat_score)

        if detection.severity == "high":
            self._log_high_threat(ctx, detection, threat_score)

        return MiddlewareResult.success()

    def _block_critical_threat(self, detection, threat_score: float) -> MiddlewareResult:
        """Block critical severity threats"""
        self.critical_blocks += 1
        return MiddlewareResult.forbidden(
            message="AI threat detection: Request blocked"
        ).with_details(
            threat_score=threat_score,
            threat_type=detection.threat_type,
            severity=detection.severity,
            confidence=detection.confidence,
        )

    def _log_high_threat(self, ctx: RequestContext, detection, threat_score: float) -> None:
        """Log high severity threats for monitoring"""
        ctx.add_metadata(
            "high_threat_detected",
            {
                "threat_type": detection.threat_type,
                "threat_score": threat_score,
                "confidence": detection.confidence,
            },
        )

    def _handle_error(self, error: Exception) -> MiddlewareResult:
        """Handle AI detector errors gracefully"""
        return MiddlewareResult.success().with_metadata("ai_threat_error", str(error))

    def get_statistics(self) -> dict:
        """Return AI threat detector statistics"""
        stats = super().get_statistics()
        stats.update(
            {
                "analyzed_count": self.analyzed_count,
                "threats_detected": self.threats_detected,
                "critical_blocks": self.critical_blocks,
                "threat_detection_rate": (
                    self.threats_detected / self.analyzed_count if self.analyzed_count > 0 else 0.0
                ),
            }
        )
        return stats
