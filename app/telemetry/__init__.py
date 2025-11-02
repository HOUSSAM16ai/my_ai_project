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

from app.telemetry.tracing import DistributedTracer
from app.telemetry.metrics import MetricsCollector
from app.telemetry.logging import StructuredLogger
from app.telemetry.events import EventTracker
from app.telemetry.performance import PerformanceMonitor

__all__ = [
    "DistributedTracer",
    "MetricsCollector",
    "StructuredLogger",
    "EventTracker",
    "PerformanceMonitor",
]
