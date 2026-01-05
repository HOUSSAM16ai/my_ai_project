# app/middleware/factory/middleware_factory.py
# ======================================================================================
# ==                    MIDDLEWARE FACTORY (v∞)                                     ==
# ======================================================================================
"""مصنع وسيط يبني خطوط أنابيب جاهزة بتوثيق واضح للمبتدئين."""

from app.middleware.core.pipeline import SmartPipeline
from app.middleware.error_handling import ErrorHandlerMiddleware, RecoveryMiddleware
from app.middleware.fastapi_observability import FastAPIObservabilityMiddleware
from app.middleware.observability import PerformanceProfiler, RequestLoggerMiddleware
from app.middleware.security import (
    AIThreatMiddleware,
    PolicyEnforcer,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    TelemetryGuard,
    WAFMiddleware,
)

class MiddlewareFactory:
    """يبني خطوط أنابيب جاهزة للاستخدام بحسب سياق البيئة."""

    @staticmethod
    def create_production_pipeline(
        config: dict[str, object] | None = None,
    ) -> SmartPipeline:
        """ينشئ خطاً متكاملاً للإنتاج مع ضبط أمن ومراقبة شامل."""
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
    def create_development_pipeline(
        config: dict[str, object] | None = None,
    ) -> SmartPipeline:
        """يوفر خط تطوير مبسطاً يركز على المراقبة وسهولة التجريب."""
        config = config or {}

        middlewares = [
            FastAPIObservabilityMiddleware(),
            RequestLoggerMiddleware(config=config.get("logging", {})),
            ErrorHandlerMiddleware(config=config.get("error_handling", {})),
        ]

        return SmartPipeline(middlewares)

    @staticmethod
    def create_minimal_pipeline() -> SmartPipeline:
        """يبني أصغر خط أنابيب ممكن مع معالج أخطاء افتراضي."""
        return SmartPipeline([ErrorHandlerMiddleware()])
