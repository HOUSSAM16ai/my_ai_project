# app/middleware/factory/middleware_factory.py
# ======================================================================================
# ==                    MIDDLEWARE FACTORY (v∞)                                     ==
# ======================================================================================
"""
مصنع الوسيط - Middleware Factory

Factory for creating preconfigured middleware pipelines.
"""

from typing import Any

from app.middleware.core.pipeline import SmartPipeline
from app.middleware.error_handling import ErrorHandlerMiddleware, RecoveryMiddleware
from app.middleware.fastapi_observability import FastAPIObservabilityMiddleware
from app.middleware.observability import (
    PerformanceProfiler,
    RequestLoggerMiddleware,
)
from app.middleware.security import (
    AIThreatMiddleware,
    PolicyEnforcer,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    TelemetryGuard,
    WAFMiddleware,
)


class MiddlewareFactory:
    """
    Middleware Factory

    Creates preconfigured middleware pipelines for common scenarios.
    """

    @staticmethod
    def create_production_pipeline(config: dict[str, Any] | None = None) -> SmartPipeline:
        """
        Create production-ready middleware pipeline

        Args:
            config: Configuration dictionary

        Returns:
            Configured SmartPipeline
        """
        config = config or {}

        middlewares = [
            PerformanceProfiler(config=config.get("performance", {})),
            TelemetryGuard(config=config.get("telemetry", {})),
            FastAPIObservabilityMiddleware(),
            RequestLoggerMiddleware(config=config.get("logging", {})),
            WAFMiddleware(config=config.get("waf", {})),
            AIThreatMiddleware(config=config.get("ai_threats", {})),
            RateLimitMiddleware(config=config.get("rate_limiting", {})),
            PolicyEnforcer(config=config.get("policies", {})),
            SecurityHeadersMiddleware(config=config.get("security_headers", {})),
            RecoveryMiddleware(config=config.get("recovery", {})),
            ErrorHandlerMiddleware(config=config.get("error_handling", {})),
        ]

        return SmartPipeline(middlewares)

    @staticmethod
    def create_development_pipeline(config: dict[str, Any] | None = None) -> SmartPipeline:
        """
        Create development middleware pipeline (minimal security)

        Args:
            config: Configuration dictionary

        Returns:
            Configured SmartPipeline
        """
        config = config or {}

        middlewares = [
            FastAPIObservabilityMiddleware(),
            RequestLoggerMiddleware(config=config.get("logging", {})),
            ErrorHandlerMiddleware(config=config.get("error_handling", {})),
        ]

        return SmartPipeline(middlewares)

    @staticmethod
    def create_minimal_pipeline() -> SmartPipeline:
        """
        Create minimal middleware pipeline

        Returns:
            Minimal SmartPipeline
        """
        return SmartPipeline([ErrorHandlerMiddleware()])
