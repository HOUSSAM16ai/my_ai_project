# app/services/deployment_orchestrator_service.py
"""
LEGACY WRAPPER - DEPRECATED
This module redirects to the new modular architecture in `app/services/deployment/`.
"""

from app.services.deployment import (
    CircuitBreakerStatus,
    CircuitState,
    DeploymentConfig,
    DeploymentOrchestrator,
    DeploymentPhase,
    DeploymentStatus,
    DeploymentStrategy,
    HealthCheckConfig,
    HealthCheckType,
    RollbackTrigger,
    ServiceVersion,
    TrafficSplit,
    get_deployment_orchestrator,
)

# Aliases for backward compatibility
# Assuming the original code might have used simpler names or different naming conventions
# Based on the review, "HealthCheck" and "CircuitBreaker" were likely used.
HealthCheck = HealthCheckConfig
CircuitBreaker = CircuitBreakerStatus

# Export all symbols to maintain backward compatibility
__all__ = [
    "CircuitBreaker",
    "CircuitBreakerStatus",
    "CircuitState",
    "DeploymentConfig",
    "DeploymentOrchestrator",
    "DeploymentPhase",
    "DeploymentStatus",
    "DeploymentStrategy",
    # Aliases
    "HealthCheck",
    "HealthCheckConfig",
    "HealthCheckType",
    "RollbackTrigger",
    "ServiceVersion",
    "TrafficSplit",
    "get_deployment_orchestrator",
]
