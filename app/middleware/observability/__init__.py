# app/middleware/observability/__init__.py
# ======================================================================================
# ==                    MIDDLEWARE OBSERVABILITY MODULE (v∞ - Aurora Edition)        ==
# ======================================================================================
"""
وحدة المراقبة - Observability Module

Comprehensive observability mesh for the superhuman middleware architecture.
Provides distributed tracing, metrics collection, structured logging, and
performance analysis.

Observability Philosophy:
    "Measure Everything, Understand Everything"
    - Distributed tracing with W3C Trace Context
    - Golden Signals metrics (latency, traffic, errors, saturation)
    - Structured logging with correlation IDs
    - ML-powered anomaly detection
    - Performance profiling and optimization
"""

from .analytics_adapter import AnalyticsAdapter
from .anomaly_inspector import AnomalyInspector
from .observability_middleware import ObservabilityMiddleware
from .performance_profiler import PerformanceProfiler
from .request_logger import RequestLoggerMiddleware
from .telemetry_bridge import TelemetryBridge

__all__ = [
    "AnalyticsAdapter",
    "AnomalyInspector",
    "ObservabilityMiddleware",
    "PerformanceProfiler",
    "RequestLoggerMiddleware",
    "TelemetryBridge",
]

__version__ = "1.0.0-aurora"
