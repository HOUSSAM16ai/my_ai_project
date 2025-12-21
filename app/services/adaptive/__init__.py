# app/services/adaptive/__init__.py
"""
AI-Driven Self-Adaptive Microservices
======================================
Hexagonal architecture implementation for adaptive microservices.

This package provides:
- Domain models and business logic
- Application services (scaling, routing, health monitoring)
- Infrastructure implementations
- Facade for backward compatibility
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
from app.services.adaptive.facade import (
    SelfAdaptiveMicroservices,
    get_adaptive_microservices,
)
from app.services.adaptive.infrastructure import (
    InMemoryMetricsRepository,
    InMemoryServiceInstanceRepository,
)

__all__ = [
    # Application
    "AIScalingEngine",
    "InMemoryMetricsRepository",
    # Infrastructure
    "InMemoryServiceInstanceRepository",
    "IntelligentRouter",
    "PredictiveHealthMonitor",
    "ScalingDecision",
    "ScalingDirection",
    # Facade
    "SelfAdaptiveMicroservices",
    # Domain
    "ServiceHealth",
    "ServiceInstance",
    "ServiceMetrics",
    "get_adaptive_microservices",
]
