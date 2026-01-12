from __future__ import annotations

import threading
from collections.abc import Callable
from datetime import UTC, datetime
from functools import wraps
from typing import Any

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


def resilient(
    circuit_breaker_name: str | None = None,
    retry_config: RetryConfig | None = None,
    bulkhead_name: str | None = None,
    fallback_chain: FallbackChain | None = None,
) -> Callable:
    """
    مزخرف لجعل الدوال مرنة | Decorator to make functions resilient

    يطبق أنماط المرونة (Circuit Breaker, Retry, Bulkhead)
    Applies resilience patterns (Circuit Breaker, Retry, Bulkhead)

    Usage:
        @resilient(
            circuit_breaker_name="database",
            retry_config=RetryConfig(max_retries=3),
            bulkhead_name="api_calls"
        )
        def my_function() -> Any:
            pass
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            service = get_resilience_service()

            # Apply resilience patterns in priority order
            if circuit_breaker_name:
                return _apply_circuit_breaker(service, circuit_breaker_name, func, args, kwargs)

            if retry_config:
                return _apply_retry(service, retry_config, func, args, kwargs)

            if bulkhead_name:
                return _apply_bulkhead(service, bulkhead_name, func, args, kwargs)

            # Default execution without resilience
            return func(*args, **kwargs)

        return wrapper

    return decorator


def _apply_circuit_breaker(
    service: DistributedResilienceService,
    circuit_breaker_name: str,
    func: Callable,
    args: tuple,
    kwargs: dict,
) -> Any:
    """
    تطبيق نمط قاطع الدائرة | Apply circuit breaker pattern

    Args:
        service: خدمة المرونة | Resilience service
        circuit_breaker_name: اسم قاطع الدائرة | Circuit breaker name
        func: الدالة المراد تنفيذها | Function to execute
        args: معاملات الدالة | Function arguments
        kwargs: معاملات مسماة | Named arguments

    Returns:
        نتيجة تنفيذ الدالة | Function execution result
    """
    cb = service.get_or_create_circuit_breaker(circuit_breaker_name)

    def func_to_call() -> Any:
        return func(*args, **kwargs)

    return cb.call(func_to_call)


def _apply_retry(
    service: DistributedResilienceService,
    retry_config: RetryConfig,
    func: Callable,
    args: tuple,
    kwargs: dict,
) -> Any:
    """
    تطبيق نمط إعادة المحاولة | Apply retry pattern

    Args:
        service: خدمة المرونة | Resilience service
        retry_config: إعدادات إعادة المحاولة | Retry configuration
        func: الدالة المراد تنفيذها | Function to execute
        args: معاملات الدالة | Function arguments
        kwargs: معاملات مسماة | Named arguments

    Returns:
        نتيجة تنفيذ الدالة | Function execution result
    """
    rm = service.get_or_create_retry_manager("default", retry_config)
    return rm.execute_with_retry(func, *args, **kwargs)


def _apply_bulkhead(
    service: DistributedResilienceService,
    bulkhead_name: str,
    func: Callable,
    args: tuple,
    kwargs: dict,
) -> Any:
    """
    تطبيق نمط الحاجز المائي | Apply bulkhead pattern

    Args:
        service: خدمة المرونة | Resilience service
        bulkhead_name: اسم الحاجز | Bulkhead name
        func: الدالة المراد تنفيذها | Function to execute
        args: معاملات الدالة | Function arguments
        kwargs: معاملات مسماة | Named arguments

    Returns:
        نتيجة تنفيذ الدالة | Function execution result
    """
    bh = service.get_or_create_bulkhead(bulkhead_name)
    return bh.execute(func, *args, **kwargs)
