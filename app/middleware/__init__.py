# ======================================================================================
# ==                    MIDDLEWARE MODULE (v∞ - Aurora Edition)                      ==
# ======================================================================================
"""
وحدة الوسيط - Middleware Module

Superhuman middleware architecture combining enterprise-grade patterns
from Meta, Palantir, Cloudflare, and OpenAI infrastructure.

Architecture Components:
- Core: Unified abstractions and pipeline orchestration
- Security: Multi-layer defense with AI-powered threat detection
- Observability: Distributed tracing, metrics, and analytics
- Error Handling: Graceful recovery and exception mapping
- Adapters: Framework-agnostic integration
- Factory: Preconfigured pipelines for common scenarios

Philosophy: "Every request is an intelligent pipeline"
"""

# ======================================================================================
# NEW ARCHITECTURE (v∞ - Aurora Edition)
# ======================================================================================

# Core components
from app.middleware.core import (
    BaseMiddleware,
    LifecycleHooks,
    MiddlewareRegistry,
    MiddlewareResult,
    RequestContext,
    ResponseFactory,
    SmartPipeline,
)

# Security mesh
from app.middleware.security import (
    AIThreatMiddleware,
    PolicyEnforcer,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    SuperhumanSecurityOrchestrator,
    TelemetryGuard,
    WAFMiddleware,
    ZeroTrustMiddleware,
)

# Observability mesh
from app.middleware.observability import (
    AnalyticsAdapter,
    AnomalyInspector,
    ObservabilityMiddleware,
    PerformanceProfiler,
    RequestLoggerMiddleware,
    TelemetryBridge,
)

# Error handling
from app.middleware.error_handling import (
    ErrorHandlerMiddleware,
    ExceptionMapper,
    RecoveryMiddleware,
)

# CORS
from app.middleware.cors import CORSMiddleware

# Adapters
from app.middleware.adapters import FlaskAdapter

# Configuration
from app.middleware.config import MiddlewareSettings

# Factory
from app.middleware.factory import MiddlewareFactory

# ======================================================================================
# BACKWARD COMPATIBILITY (Legacy v1.0)
# ======================================================================================

# Keep existing imports for backward compatibility
from app.middleware.cors_config import setup_cors
from app.middleware.error_handler import setup_error_handlers
from app.middleware.request_logger import setup_request_logging

# ======================================================================================
# EXPORTS
# ======================================================================================

__all__ = [
    # Core
    "BaseMiddleware",
    "RequestContext",
    "MiddlewareResult",
    "SmartPipeline",
    "MiddlewareRegistry",
    "LifecycleHooks",
    "ResponseFactory",
    # Security
    "SuperhumanSecurityOrchestrator",
    "WAFMiddleware",
    "AIThreatMiddleware",
    "RateLimitMiddleware",
    "ZeroTrustMiddleware",
    "PolicyEnforcer",
    "SecurityHeadersMiddleware",
    "TelemetryGuard",
    # Observability
    "ObservabilityMiddleware",
    "RequestLoggerMiddleware",
    "TelemetryBridge",
    "AnomalyInspector",
    "PerformanceProfiler",
    "AnalyticsAdapter",
    # Error Handling
    "ErrorHandlerMiddleware",
    "ExceptionMapper",
    "RecoveryMiddleware",
    # Other
    "CORSMiddleware",
    "FlaskAdapter",
    "MiddlewareSettings",
    "MiddlewareFactory",
    # Legacy (backward compatibility)
    "setup_error_handlers",
    "setup_cors",
    "setup_request_logging",
]

__version__ = "1.0.0-aurora"
