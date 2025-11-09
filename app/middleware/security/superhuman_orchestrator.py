# app/middleware/security/superhuman_orchestrator.py
# ======================================================================================
# ==                    SUPERHUMAN SECURITY ORCHESTRATOR (v∞)                       ==
# ======================================================================================
"""
منسق الأمان الخارق - Superhuman Security Orchestrator

Unified security mesh combining all security components into a
cohesive, intelligent security system. Orchestrates WAF, AI threats,
rate limiting, Zero Trust, policy enforcement, and telemetry.

Architecture: Layered Defense with AI Adaptation
"""

from typing import Any

from flask import Flask, g

from app.middleware.core.context import RequestContext
from app.middleware.core.pipeline import SmartPipeline
from app.middleware.core.response_factory import ResponseFactory

from .ai_threat_middleware import AIThreatMiddleware
from .policy_enforcer import PolicyEnforcer
from .rate_limit_middleware import RateLimitMiddleware
from .security_headers import SecurityHeadersMiddleware
from .telemetry_guard import TelemetryGuard
from .waf_middleware import WAFMiddleware
from .zero_trust_middleware import ZeroTrustMiddleware


class SuperhumanSecurityOrchestrator:
    """
    Unified security mesh orchestrator

    Combines multiple security layers into an adaptive,
    intelligent security system that rivals and exceeds
    commercial security platforms.

    Features:
    - Multi-layer defense (WAF, AI, Rate Limiting, Zero Trust)
    - Policy-based access control
    - Comprehensive telemetry and audit logging
    - Framework-agnostic design
    - Zero-config defaults with full customization
    """

    def __init__(
        self,
        app: Flask | None = None,
        config: dict[str, Any] | None = None,
    ):
        """
        Initialize security orchestrator

        Args:
            app: Flask application (optional, can init later)
            config: Configuration dictionary
        """
        self.config = config or {}

        # Initialize security pipeline
        self.pipeline = self._build_security_pipeline()

        # Statistics tracking
        self.stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "successful_requests": 0,
        }

        if app:
            self.init_app(app)

    def _build_security_pipeline(self) -> SmartPipeline:
        """
        Build the security middleware pipeline

        Returns:
            Configured SmartPipeline instance
        """
        middlewares = []

        # Layer 0: Telemetry (track everything)
        telemetry_config = self.config.get("telemetry", {})
        middlewares.append(TelemetryGuard(config=telemetry_config))

        # Layer 1: Web Application Firewall
        if self.config.get("enable_waf", True):
            waf_config = self.config.get("waf", {})
            middlewares.append(WAFMiddleware(config=waf_config))

        # Layer 2: AI Threat Detection
        if self.config.get("enable_ai_threats", True):
            ai_config = self.config.get("ai_threats", {})
            middlewares.append(AIThreatMiddleware(config=ai_config))

        # Layer 3: Rate Limiting
        if self.config.get("enable_rate_limiting", True):
            rate_config = self.config.get("rate_limiting", {})
            middlewares.append(RateLimitMiddleware(config=rate_config))

        # Layer 4: Zero Trust (optional, per-route)
        if self.config.get("enable_zero_trust", False):
            zt_config = self.config.get("zero_trust", {})
            zt_config["secret_key"] = self.config.get("secret_key", "change-me")
            middlewares.append(ZeroTrustMiddleware(config=zt_config))

        # Layer 5: Policy Enforcement
        if self.config.get("enable_policy_enforcement", True):
            policy_config = self.config.get("policies", {})
            middlewares.append(PolicyEnforcer(config={"policies": policy_config}))

        # Layer 6: Security Headers
        if self.config.get("enable_security_headers", True):
            headers_config = self.config.get("security_headers", {})
            middlewares.append(SecurityHeadersMiddleware(config=headers_config))

        return SmartPipeline(middlewares)

    def init_app(self, app: Flask):
        """
        Initialize orchestrator with Flask application

        Args:
            app: Flask application instance
        """

        @app.before_request
        def security_before_request():
            """Process request through security pipeline"""
            return self.process_request()

        @app.after_request
        def security_after_request(response):
            """Add security headers to response"""
            return self.process_response(response)

        # Add security stats endpoint
        @app.route("/api/security/stats")
        def security_stats():
            """Get security statistics"""
            from flask import jsonify

            return jsonify(self.get_statistics())

        # Add security events endpoint
        @app.route("/api/security/events")
        def security_events():
            """Get recent security events"""
            from flask import jsonify, request

            limit = request.args.get("limit", 100, type=int)
            telemetry = self._get_telemetry_guard()

            if telemetry:
                events = telemetry.get_recent_events(limit)
                return jsonify({"events": events, "count": len(events)})

            return jsonify({"events": [], "count": 0})

        # Add audit trail endpoint
        @app.route("/api/security/audit")
        def security_audit():
            """Get audit trail"""
            from flask import jsonify, request

            limit = request.args.get("limit", 100, type=int)
            telemetry = self._get_telemetry_guard()

            if telemetry:
                audit = telemetry.get_audit_trail(limit)
                return jsonify({"audit": audit, "count": len(audit)})

            return jsonify({"audit": [], "count": 0})

        app.logger.info("🔐 Superhuman Security Orchestrator initialized")
        app.logger.info(f"✅ Active middleware layers: {len(self.pipeline.middlewares)}")
        app.logger.info(
            f"🛡️ Security layers: {', '.join(self.pipeline.get_middleware_list())}"
        )

    def process_request(self):
        """
        Process incoming request through security pipeline

        Returns:
            Flask response if blocked, None if allowed
        """
        from flask import request

        self.stats["total_requests"] += 1

        # Create request context
        ctx = RequestContext.from_flask_request(request)

        # Run security pipeline
        result = self.pipeline.run(ctx)

        # Store context in Flask g for response processing
        g.security_ctx = ctx
        g.security_result = result

        # Handle blocked requests
        if not result.is_success:
            self.stats["blocked_requests"] += 1
            return ResponseFactory.from_middleware_result(result, framework="flask")

        self.stats["successful_requests"] += 1
        return None  # Continue to route handler

    def process_response(self, response):
        """
        Process response and add security headers

        Args:
            response: Flask response object

        Returns:
            Modified response with security headers
        """
        # Add security headers from context
        if hasattr(g, "security_ctx"):
            security_headers = g.security_ctx.get_metadata("security_headers", {})
            for key, value in security_headers.items():
                response.headers[key] = value

            # Add trace ID for debugging
            if g.security_ctx.trace_id:
                response.headers["X-Trace-ID"] = g.security_ctx.trace_id

            # Add powered by header
            response.headers["X-Security-System"] = "Superhuman v∞"

        return response

    def _get_telemetry_guard(self) -> TelemetryGuard | None:
        """Get TelemetryGuard instance from pipeline"""
        for mw in self.pipeline.middlewares:
            if isinstance(mw, TelemetryGuard):
                return mw
        return None

    def get_statistics(self) -> dict[str, Any]:
        """
        Get comprehensive security statistics

        Returns:
            Dictionary of statistics from all components
        """
        stats = {
            "orchestrator": {
                "total_requests": self.stats["total_requests"],
                "blocked_requests": self.stats["blocked_requests"],
                "successful_requests": self.stats["successful_requests"],
                "block_rate": (
                    self.stats["blocked_requests"] / self.stats["total_requests"]
                    if self.stats["total_requests"] > 0
                    else 0.0
                ),
            },
            "pipeline": self.pipeline.get_statistics(),
            "middleware": {},
        }

        # Get stats from each middleware
        for mw in self.pipeline.middlewares:
            stats["middleware"][mw.name] = mw.get_statistics()

        return stats

    def reset_statistics(self):
        """Reset all statistics"""
        self.stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "successful_requests": 0,
        }
        self.pipeline.reset_statistics()


# Convenience function for easy initialization
def create_security_orchestrator(
    app: Flask | None = None,
    secret_key: str | None = None,
    **kwargs,
) -> SuperhumanSecurityOrchestrator:
    """
    Create and configure security orchestrator

    Args:
        app: Flask application
        secret_key: Secret key for Zero Trust
        **kwargs: Additional configuration options

    Returns:
        Configured SuperhumanSecurityOrchestrator
    """
    config = kwargs.copy()
    if secret_key:
        config["secret_key"] = secret_key

    return SuperhumanSecurityOrchestrator(app=app, config=config)
