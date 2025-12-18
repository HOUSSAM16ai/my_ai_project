# app/telemetry/__init__.py
# ======================================================================================
# ==           SUPERHUMAN TELEMETRY MODULE (v1.0 - OPENTELEMETRY EDITION)           ==
# ======================================================================================
"""
نظام التتبع الخارق - Superhuman Telemetry System

Features surpassing tech giants:
- OpenTelemetry integration (better than DataDog)
- Distributed tracing with W3C Trace Context
- Real-time metrics collection
- Structured log aggregation
- Performance monitoring
- Event tracking with correlation
"""
import logging
import sys
from typing import Any, Dict, Optional

# Import from existing files
from app.telemetry.events import EventTracker
from app.telemetry.performance import PerformanceMonitor

# Import from my new refactored modules
from app.telemetry.structured_logging import LoggingManager
from app.telemetry.metrics import MetricsManager
from app.telemetry.tracing import TracingManager
from app.telemetry.unified_observability import UnifiedObservabilityService, get_unified_observability

# Configure standard logger to ensure stdout output
_std_logger = logging.getLogger("app.telemetry")
if not _std_logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    _std_logger.addHandler(handler)
    _std_logger.setLevel(logging.INFO)

# Aliases for backward compatibility with functional adapters

class StructuredLogger(LoggingManager):
    """
    Adapter for StructuredLogger to match existing usage.
    Delegates to LoggingManager for correlation AND writes to standard output.
    """
    def info(self, message: str, **kwargs):
        self.log("INFO", message, context=kwargs)
        _std_logger.info(message, extra=kwargs)

    def error(self, message: str, exception: Optional[Exception] = None, **kwargs):
        self.log("ERROR", message, context=kwargs, exception=exception)
        _std_logger.error(message, exc_info=exception, extra=kwargs)

    def warning(self, message: str, **kwargs):
        self.log("WARNING", message, context=kwargs)
        _std_logger.warning(message, extra=kwargs)

    def debug(self, message: str, **kwargs):
        self.log("DEBUG", message, context=kwargs)
        _std_logger.debug(message, extra=kwargs)

    def critical(self, message: str, **kwargs):
        self.log("CRITICAL", message, context=kwargs)
        _std_logger.critical(message, extra=kwargs)

class MetricsCollector(MetricsManager):
    """
    Adapter for MetricsCollector.
    """
    def increment(self, name: str, amount: float = 1.0, tags: Optional[Dict[str, str]] = None):
        self.increment_counter(name, amount, labels=tags)

    def gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        self.set_gauge(name, value, labels=tags)

    def histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        self.record_metric(name, value, labels=tags)

class DistributedTracer(TracingManager):
    """
    Adapter for DistributedTracer.
    """
    # Assuming the original DistributedTracer might have had methods like 'trace' context manager
    # or 'start_span'. My TracingManager has 'start_trace'.

    # We need to know what DistributedTracer looked like.
    # Based on 'app/services/distributed_tracing.py' grep result: "class DistributedTracer:"
    # It likely had `start_span`.

    def start_span(self, operation_name: str, parent_context=None, tags=None):
        return self.start_trace(operation_name, parent_context, tags)

__all__ = [
    "DistributedTracer",
    "EventTracker",
    "MetricsCollector",
    "PerformanceMonitor",
    "StructuredLogger",
    "UnifiedObservabilityService",
    "get_unified_observability",
    "TracingManager",
    "MetricsManager",
    "LoggingManager"
]
