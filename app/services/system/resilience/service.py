from __future__ import annotations

from typing import Any


import threading
from collections.abc import Callable
from datetime import UTC, datetime
from functools import wraps

from app.services.resilience.bulkhead import Bulkhead, BulkheadConfig
from app.services.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerConfig
from app.services.resilience.fallback import FallbackChain
from app.services.resilience.health import HealthChecker
from app.services.resilience.retry import RetryConfig, RetryManager
from app.services.resilience.timeout import AdaptiveTimeout

class DistributedResilienceService:
    """
    المدير الخارق لجميع أنماط المرونة في الأنظمة الموزعة

    Integrates:
    - Circuit Breakers
    - Retry with Backoff
    - Bulkheads
    - Adaptive Timeouts
    - Fallback Chains
    - Rate Limiting
    - Health Checks
    """

    def __init__(self):
        self.circuit_breakers: dict[str, CircuitBreaker] = {}
        self.retry_managers: dict[str, RetryManager] = {}
        self.bulkheads: dict[str, Bulkhead] = {}
        self.adaptive_timeouts: dict[str, AdaptiveTimeout] = {}
        self.fallback_chains: dict[str, FallbackChain] = {}
        self.rate_limiters: dict[str, Any] = {}
        self.health_checkers: dict[str, HealthChecker] = {}
        self._lock = threading.RLock()

    def get_or_create_circuit_breaker(
        self, name: str, config: CircuitBreakerConfig | None = None
    ) -> CircuitBreaker:
        """Get or create circuit breaker"""
        with self._lock:
            if name not in self.circuit_breakers:
                config = config or CircuitBreakerConfig()
                self.circuit_breakers[name] = CircuitBreaker(name, config)
            return self.circuit_breakers[name]

    def get_or_create_retry_manager(
        self, name: str, config: RetryConfig | None = None
    ) -> RetryManager:
        """Get or create retry manager"""
        with self._lock:
            if name not in self.retry_managers:
                config = config or RetryConfig()
                self.retry_managers[name] = RetryManager(config)
            return self.retry_managers[name]

    def get_or_create_bulkhead(self, name: str, config: BulkheadConfig | None = None) -> Bulkhead:
        """Get or create bulkhead"""
        with self._lock:
            if name not in self.bulkheads:
                config = config or BulkheadConfig()
                self.bulkheads[name] = Bulkhead(name, config)
            return self.bulkheads[name]

    def get_comprehensive_stats(self) -> dict[str, Any]:
        """Get comprehensive resilience statistics"""
        stats: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "circuit_breakers": {},
            "retry_managers": {},
            "bulkheads": {},
            "adaptive_timeouts": {},
        }

        with self._lock:
            for name, cb in self.circuit_breakers.items():
                stats["circuit_breakers"][name] = cb.get_stats()

            for name, rm in self.retry_managers.items():
                stats["retry_managers"][name] = rm.retry_budget.get_stats()

            for name, bh in self.bulkheads.items():
                stats["bulkheads"][name] = bh.get_stats()

            for name, at in self.adaptive_timeouts.items():
                stats["adaptive_timeouts"][name] = at.get_stats()

        return stats

# ======================================================================================
# GLOBAL INSTANCE
# ======================================================================================

# Singleton instance for global access
_resilience_service: DistributedResilienceService | None = None

def get_resilience_service() -> DistributedResilienceService:
    """Get global resilience service instance"""
    global _resilience_service
    if _resilience_service is None:
        _resilience_service = DistributedResilienceService()
    return _resilience_service

# TODO: Split this function (49 lines) - KISS principle
def resilient(
    circuit_breaker_name: str | None = None,
    retry_config: RetryConfig | None = None,
    bulkhead_name: str | None = None,
    fallback_chain: FallbackChain | None = None,  # noqa: unused variable
) -> None:
    """
    Decorator to make functions resilient

    Usage:
        @resilient(
            circuit_breaker_name="database",
            retry_config=RetryConfig(max_retries=3),
            bulkhead_name="api_calls"
        )
        def my_function() -> None:
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> None:
            # Use global singleton service for component reuse
            service = get_resilience_service()

            # Apply circuit breaker
            if circuit_breaker_name:
                cb = service.get_or_create_circuit_breaker(circuit_breaker_name)

                def func_to_call() -> None:
                    return func(*args, **kwargs)

                return cb.call(func_to_call)

            # Apply retry
            if retry_config:
                rm = service.get_or_create_retry_manager("default", retry_config)
                return rm.execute_with_retry(func, *args, **kwargs)

            # Apply bulkhead
            if bulkhead_name:
                bh = service.get_or_create_bulkhead(bulkhead_name)
                return bh.execute(func, *args, **kwargs)

            # Default execution
            return func(*args, **kwargs)

        return wrapper

    return decorator
