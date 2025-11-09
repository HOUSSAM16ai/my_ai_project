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
        """
        Analyze request for AI-detected threats

        Args:
            ctx: Request context

        Returns:
            MiddlewareResult indicating threat level
        """
        self.analyzed_count += 1

        # Skip AI analysis for health checks
        if ctx.path in ["/health", "/api/health", "/ping"]:
            return MiddlewareResult.success()

        try:
            # Analyze request
            threat_score, detection = self.ai_detector.analyze_request(
                ctx._raw_request,
                ctx.ip_address,
            )

            # Store threat score in context for logging
            ctx.add_metadata("threat_score", threat_score)

            if detection:
                self.threats_detected += 1

                # Block critical threats
                if detection.severity == "critical":
                    self.critical_blocks += 1
                    return MiddlewareResult.forbidden(
                        message="AI threat detection: Request blocked"
                    ).with_details(
                        threat_score=threat_score,
                        threat_type=detection.threat_type,
                        severity=detection.severity,
                        confidence=detection.confidence,
                    )

                # Log high severity threats but allow
                if detection.severity == "high":
                    ctx.add_metadata("high_threat_detected", {
                        "threat_type": detection.threat_type,
                        "threat_score": threat_score,
                        "confidence": detection.confidence,
                    })

            return MiddlewareResult.success()

        except Exception as e:
            # If AI detector fails, allow request but log error
            return MiddlewareResult.success().with_metadata(
                "ai_threat_error", str(e)
            )

    def get_statistics(self) -> dict:
        """Return AI threat detector statistics"""
        stats = super().get_statistics()
        stats.update(
            {
                "analyzed_count": self.analyzed_count,
                "threats_detected": self.threats_detected,
                "critical_blocks": self.critical_blocks,
                "threat_detection_rate": (
                    self.threats_detected / self.analyzed_count
                    if self.analyzed_count > 0
                    else 0.0
                ),
            }
        )
        return stats
