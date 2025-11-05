# app/middleware/superhuman_security.py
# ======================================================================================
# ==        SUPERHUMAN SECURITY MIDDLEWARE (v1.0 - INTEGRATION EDITION)             ==
# ======================================================================================
"""
وسيط الأمان الخارق - Superhuman Security Middleware

Integrates all security components into Flask:
- WAF (Web Application Firewall)
- Adaptive Rate Limiting
- Zero Trust Authentication
- AI Threat Detection
- Telemetry & Analytics
"""

import time
from collections.abc import Callable
from functools import wraps
from typing import Any

from flask import Flask, g, jsonify, request

from app.analysis.anomaly_detector import AnomalyDetector
from app.analysis.pattern_recognizer import PatternRecognizer
from app.security.rate_limiter import AdaptiveRateLimiter, UserTier
from app.security.threat_detector import AIThreatDetector
from app.security.waf import WebApplicationFirewall
from app.security.zero_trust import ZeroTrustAuthenticator
from app.telemetry.events import EventTracker
from app.telemetry.logging import StructuredLogger
from app.telemetry.metrics import MetricsCollector
from app.telemetry.tracing import DistributedTracer


class SuperhumanSecurityMiddleware:
    """
    وسيط الأمان الخارق - Superhuman Security Middleware

    Integrates all security and telemetry components
    Better than any single commercial solution
    """

    def __init__(
        self,
        app: Flask | None = None,
        secret_key: str | None = None,
        enable_waf: bool = True,
        enable_rate_limiting: bool = True,
        enable_zero_trust: bool = True,
        enable_ai_detection: bool = True,
        enable_telemetry: bool = True,
        enable_analytics: bool = True,
    ):
        # Initialize components
        self.waf = WebApplicationFirewall() if enable_waf else None
        self.rate_limiter = AdaptiveRateLimiter() if enable_rate_limiting else None
        self.zero_trust = (
            ZeroTrustAuthenticator(secret_key or "change-me-in-production")
            if enable_zero_trust
            else None
        )
        self.ai_detector = AIThreatDetector() if enable_ai_detection else None

        # Telemetry components
        self.tracer = DistributedTracer() if enable_telemetry else None
        self.metrics = MetricsCollector() if enable_telemetry else None
        self.logger = StructuredLogger() if enable_telemetry else None
        self.events = EventTracker() if enable_telemetry else None

        # Analytics components
        self.anomaly_detector = AnomalyDetector() if enable_analytics else None
        self.pattern_recognizer = PatternRecognizer() if enable_analytics else None

        # Configuration
        self.enabled_features = {
            "waf": enable_waf,
            "rate_limiting": enable_rate_limiting,
            "zero_trust": enable_zero_trust,
            "ai_detection": enable_ai_detection,
            "telemetry": enable_telemetry,
            "analytics": enable_analytics,
        }

        if app:
            self.init_app(app)

    def init_app(self, app: Flask):
        """Initialize middleware with Flask app"""

        # Register before_request handler
        @app.before_request
        def before_request():
            return self.process_request()

        # Register after_request handler
        @app.after_request
        def after_request(response):
            return self.process_response(response)

        # Register error handler
        @app.errorhandler(403)
        def handle_forbidden(error):
            return (
                jsonify(
                    {"error": "Access Forbidden", "message": "Security check failed", "code": 403}
                ),
                403,
            )

        # Register error handler for rate limiting
        @app.errorhandler(429)
        def handle_rate_limit(error):
            return (
                jsonify(
                    {"error": "Too Many Requests", "message": "Rate limit exceeded", "code": 429}
                ),
                429,
            )

        # Add stats endpoint
        @app.route("/api/security/stats")
        def security_stats():
            return jsonify(self.get_statistics())

    def process_request(self):
        """Process incoming request through security layers"""
        # Start telemetry
        if self.tracer:
            trace_id, span_id = self.tracer.start_trace(
                f"{request.method} {request.path}",
                attributes={
                    "http.method": request.method,
                    "http.url": request.url,
                    "http.user_agent": request.headers.get("User-Agent", ""),
                },
            )
            g.trace_id = trace_id
            g.span_id = span_id
            g.request_start_time = time.time()

        # Get IP address
        ip_address = request.remote_addr or "unknown"

        # Layer 1: Web Application Firewall
        if self.waf:
            is_safe, attack = self.waf.check_request(request)
            if not is_safe:
                # Log security event
                if self.events:
                    self.events.track_security_event(
                        name="waf_block",
                        severity="high",
                        properties={
                            "ip": ip_address,
                            "attack_type": attack.attack_type if attack else "unknown",
                            "endpoint": request.path,
                        },
                    )

                # Record metric
                if self.metrics:
                    self.metrics.inc_counter("security_threats_detected", labels={"type": "waf"})

                # End span with error
                if self.tracer and hasattr(g, "span_id"):
                    self.tracer.end_span(
                        g.span_id, status="error", status_message="WAF blocked request"
                    )

                return (
                    jsonify(
                        {
                            "error": "Security Violation",
                            "message": "Request blocked by WAF",
                            "code": 403,
                        }
                    ),
                    403,
                )

        # Layer 2: AI Threat Detection
        if self.ai_detector:
            threat_score, detection = self.ai_detector.analyze_request(request, ip_address)

            if detection and detection.severity == "critical":
                # Log security event
                if self.events:
                    self.events.track_security_event(
                        name="ai_threat_detected",
                        severity="critical",
                        properties={
                            "ip": ip_address,
                            "threat_score": threat_score,
                            "threat_type": detection.threat_type,
                        },
                    )

                # Record metric
                if self.metrics:
                    self.metrics.inc_counter("security_threats_detected", labels={"type": "ai"})

                return (
                    jsonify(
                        {
                            "error": "Security Threat Detected",
                            "message": "Request blocked by AI threat detector",
                            "code": 403,
                        }
                    ),
                    403,
                )

        # Layer 3: Rate Limiting
        if self.rate_limiter:
            # Determine user tier (placeholder - integrate with your auth system)
            user_tier = UserTier.FREE
            user_id = None

            # Check if user is authenticated (implement based on your auth)
            # if hasattr(g, 'current_user') and g.current_user:
            #     user_id = str(g.current_user.id)
            #     user_tier = UserTier.PREMIUM  # Map from user data

            is_allowed, info = self.rate_limiter.check_rate_limit(request, user_id, user_tier)

            if not is_allowed:
                # Log event
                if self.events:
                    self.events.track_security_event(
                        name="rate_limit_exceeded",
                        severity="medium",
                        properties={
                            "ip": ip_address,
                            "tier": user_tier.value,
                        },
                    )

                # Record metric
                if self.metrics:
                    self.metrics.inc_counter("rate_limit_exceeded")

                return (
                    jsonify(
                        {
                            "error": "Rate Limit Exceeded",
                            "message": "Too many requests",
                            "retry_after": info.get("reset_time", 60),
                            "code": 429,
                        }
                    ),
                    429,
                )

            # Store rate limit info in context
            g.rate_limit_info = info

        # Layer 4: Zero Trust (for authenticated endpoints)
        # This is optional and should be applied to specific routes
        # See require_zero_trust decorator below

        # All checks passed - log successful request
        if self.events:
            self.events.track_user_event(
                name="request_processed",
                user_id=user_id or ip_address,
                properties={
                    "method": request.method,
                    "path": request.path,
                },
            )

        # Record request metric
        if self.metrics:
            self.metrics.inc_counter(
                "http_requests_total",
                labels={
                    "method": request.method,
                    "endpoint": request.path,
                },
            )

        return None  # Continue processing

    def process_response(self, response):
        """Process response and collect telemetry"""
        # Calculate request duration
        if hasattr(g, "request_start_time"):
            duration = time.time() - g.request_start_time

            # Record duration metric
            if self.metrics:
                self.metrics.observe_histogram(
                    "http_request_duration_seconds",
                    duration,
                    labels={
                        "method": request.method,
                        "endpoint": request.path,
                        "status": str(response.status_code),
                    },
                )

            # Check for anomalies
            if self.anomaly_detector:
                metric_name = f"latency_{request.path}"
                is_anomaly, anomaly = self.anomaly_detector.check_value(
                    metric_name,
                    duration * 1000,  # Convert to ms
                )

                if is_anomaly and anomaly:
                    # Log anomaly
                    if self.logger:
                        self.logger.warning(
                            f"Latency anomaly detected: {duration * 1000:.2f}ms",
                            context={
                                "endpoint": request.path,
                                "anomaly_score": anomaly.score,
                                "severity": anomaly.severity.value,
                            },
                            trace_id=getattr(g, "trace_id", None),
                            span_id=getattr(g, "span_id", None),
                        )

            # Pattern recognition
            if self.pattern_recognizer:
                patterns = self.pattern_recognizer.analyze_traffic_pattern(
                    f"traffic_{request.path}", 1.0
                )

                for pattern in patterns:
                    if pattern.severity in ["high", "critical"]:
                        # Log pattern
                        if self.logger:
                            self.logger.warning(
                                f"Pattern detected: {pattern.description}",
                                context={
                                    "pattern_type": pattern.pattern_type.value,
                                    "confidence": pattern.confidence,
                                },
                                trace_id=getattr(g, "trace_id", None),
                            )

        # End trace span
        if self.tracer and hasattr(g, "span_id"):
            status = "ok" if response.status_code < 400 else "error"
            self.tracer.end_span(g.span_id, status=status)

        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Add trace ID to response headers (for debugging)
        if hasattr(g, "trace_id"):
            response.headers["X-Trace-ID"] = g.trace_id

        return response

    def require_zero_trust(self, f: Callable) -> Callable:
        """Decorator to enforce zero-trust authentication"""

        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not self.zero_trust:
                return f(*args, **kwargs)

            # Check for session
            session_id = request.headers.get("X-Session-ID")

            if not session_id:
                return (
                    jsonify(
                        {
                            "error": "Authentication Required",
                            "message": "Zero-trust session required",
                            "code": 401,
                        }
                    ),
                    401,
                )

            # Continuous verification
            is_valid, session = self.zero_trust.continuous_verify(session_id, request)

            if not is_valid:
                return (
                    jsonify(
                        {
                            "error": "Authentication Failed",
                            "message": "Continuous verification failed",
                            "code": 401,
                        }
                    ),
                    401,
                )

            # Store session in context
            g.zero_trust_session = session

            return f(*args, **kwargs)

        return decorated_function

    def get_statistics(self) -> dict[str, Any]:
        """Get statistics from all components"""
        stats = {"features_enabled": self.enabled_features, "components": {}}

        if self.waf:
            stats["components"]["waf"] = self.waf.get_statistics()

        if self.rate_limiter:
            stats["components"]["rate_limiter"] = self.rate_limiter.get_statistics()

        if self.zero_trust:
            stats["components"]["zero_trust"] = self.zero_trust.get_statistics()

        if self.ai_detector:
            stats["components"]["ai_detector"] = self.ai_detector.get_statistics()

        if self.tracer:
            stats["components"]["tracer"] = self.tracer.get_statistics()

        if self.metrics:
            stats["components"]["metrics"] = self.metrics.get_statistics()

        if self.events:
            stats["components"]["events"] = self.events.get_statistics()

        if self.anomaly_detector:
            stats["components"]["anomaly_detector"] = self.anomaly_detector.get_statistics()

        if self.pattern_recognizer:
            stats["components"]["pattern_recognizer"] = self.pattern_recognizer.get_statistics()

        return stats


# Global instance (will be initialized in app factory)
superhuman_security = None


def init_superhuman_security(app: Flask, **kwargs) -> SuperhumanSecurityMiddleware:
    """Initialize superhuman security middleware"""
    global superhuman_security

    superhuman_security = SuperhumanSecurityMiddleware(app=app, **kwargs)

    app.logger.info("🚀 Superhuman Security & Telemetry System initialized")
    app.logger.info(f"✅ Enabled features: {superhuman_security.enabled_features}")

    return superhuman_security
