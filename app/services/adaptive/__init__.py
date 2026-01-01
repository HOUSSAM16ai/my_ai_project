# app/services/adaptive/__init__.py
"""
AI-Driven Self-Adaptive Microservices - SOLID Principles Applied
===============================================================
Simplified architecture using KISS principle.

This package provides:
- Domain models and business logic
- Application services (scaling, routing, health monitoring) - Direct Access
- Infrastructure implementations

Usage:
    from app.services.adaptive import (
        AIScalingEngine,
        IntelligentRouter,
        PredictiveHealthMonitor
    )
"""

from app.services.adaptive.application import (
    AIScalingEngine,
    IntelligentRouter,
    PredictiveHealthMonitor,
)
from app.services.adaptive.domain import (
    ScalingDecision,
    ScalingDirection,
    ServiceHealth,
    ServiceInstance,
    ServiceMetrics,
)
from app.services.adaptive.infrastructure import (
    InMemoryMetricsRepository,
    InMemoryServiceInstanceRepository,
)

__all__ = [
    # Application Services (Direct Access - KISS)
    "AIScalingEngine",
    "IntelligentRouter",
    "PredictiveHealthMonitor",
    # Domain Models
    "ScalingDecision",
    "ScalingDirection",
    "ServiceHealth",
    "ServiceInstance",
    "ServiceMetrics",
    # Infrastructure
    "InMemoryMetricsRepository",
    "InMemoryServiceInstanceRepository",
]
