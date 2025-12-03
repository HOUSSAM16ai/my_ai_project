# app/core/resilience/__init__.py
"""
RESILIENCE MODULE — CENTRALIZED FAULT TOLERANCE
================================================

This module provides centralized resilience patterns for the entire application.
Eliminates duplicate circuit breaker and bulkhead implementations.

EXPORTS:
- CircuitBreaker: Circuit breaker pattern implementation
- CircuitBreakerRegistry: Singleton registry for circuit breakers
- BulkheadExecutor: Bulkhead pattern for resource isolation
- RetryPolicy: Configurable retry strategies
"""

from .circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerRegistry,
    CircuitState,
    get_circuit_breaker,
)

__all__ = [
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerRegistry",
    "CircuitState",
    "get_circuit_breaker",
]
