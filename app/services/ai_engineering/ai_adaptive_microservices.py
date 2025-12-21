# app/services/ai_adaptive_microservices.py
"""
🚀 SUPERHUMAN AI-DRIVEN SELF-ADAPTIVE MICROSERVICES - LEGACY COMPATIBILITY SHIM
===============================================================================

نظام خدمات ذاتية التكيف مدعومة بالذكاء الاصطناعي
This file maintains backward compatibility by delegating to the refactored
hexagonal architecture in app/services/adaptive/

Original file: 703 lines
Refactored: Delegates to adaptive/ module

SOLID PRINCIPLES APPLIED:
  - Single Responsibility: Each component has one clear purpose
  - Open/Closed: Open for extension via ports/adapters
  - Liskov Substitution: All implementations are interchangeable
  - Interface Segregation: Small focused protocols
  - Dependency Inversion: Depends on abstractions (ports)

For new code, import from: app.services.adaptive
This shim exists for backward compatibility only.
"""

from __future__ import annotations

# Re-export everything from the refactored hexagonal architecture
from app.services.adaptive import (
    # Application services
    AIScalingEngine,
    InMemoryMetricsRepository,
    # Infrastructure
    InMemoryServiceInstanceRepository,
    IntelligentRouter,
    PredictiveHealthMonitor,
    ScalingDecision,
    ScalingDirection,
    # Main facade (most common usage)
    SelfAdaptiveMicroservices,
    # Domain models
    ServiceHealth,
    ServiceInstance,
    ServiceMetrics,
    get_adaptive_microservices,
)

__all__ = [
    # Enums
    "ServiceHealth",
    "ScalingDirection",
    # Models
    "ServiceMetrics",
    "ScalingDecision",
    "ServiceInstance",
    # Application services
    "AIScalingEngine",
    "IntelligentRouter",
    "PredictiveHealthMonitor",
    # Infrastructure
    "InMemoryServiceInstanceRepository",
    "InMemoryMetricsRepository",
    # Service facade
    "SelfAdaptiveMicroservices",
    "get_adaptive_microservices",
]
