# app/services/distributed_resilience_service.py
# ======================================================================================
# ==    SUPERHUMAN DISTRIBUTED SYSTEMS RESILIENCE SERVICE (v1.0 - ULTIMATE EDITION) ==
# ======================================================================================
# PRIME DIRECTIVE:
#   نظام هندسة التخطيط للفشل في الأنظمة الموزعة - خارق يتفوق على Netflix و Google و AWS
#   ✨ المميزات الخارقة:
#   - Circuit Breaker Pattern (CLOSED/OPEN/HALF_OPEN)
#   - Exponential Backoff with Jitter
#   - Retry Budget Management
#   - Idempotency Keys
#   - Bulkhead Pattern (Resource Isolation)
#   - Adaptive Timeout Management
#   - Multi-Level Fallback Chain
#   - Health Check System (Liveness/Readiness/Deep)
#   - Rate Limiting (Token Bucket, Sliding Window, Leaky Bucket)
#   - Load Shedding with Priority Queues
#   - Data Consistency (CAP, Eventual Consistency, CRDTs)
#   - Comprehensive Observability
#
# TARGET METRICS:
#   - Netflix-level: 99.99% Uptime
#   - Google-level: 99.999% Availability (5-nines)
#   - AWS-level: 99.999999999% Durability (11-nines)
#
# ======================================================================================

# This file is now a facade for the modular package in app/services/resilience/
# to maintain backward compatibility.

from app.services.resilience import (
    AdaptiveTimeout,
    Bulkhead,
    BulkheadConfig,
    BulkheadFullError,
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerOpenError,
    CircuitBreakerState,
    CircuitState,
    DistributedResilienceService,
    FallbackChain,
    FallbackLevel,
    HealthCheckConfig,
    HealthChecker,
    HealthCheckResult,
    HealthCheckType,
    IdempotencyKey,
    LatencyMetrics,
    LeakyBucket,
    PriorityLevel,
    RateLimitConfig,
    RetryAttempt,
    RetryBudget,
    RetryBudgetExhaustedError,
    RetryConfig,
    RetryManager,
    RetryStrategy,
    RetryableError,
    SlidingWindowCounter,
    TimeoutConfig,
    TokenBucket,
    get_resilience_service,
    resilient,
)

__all__ = [
    "AdaptiveTimeout",
    "Bulkhead",
    "BulkheadConfig",
    "BulkheadFullError",
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitBreakerOpenError",
    "CircuitBreakerState",
    "CircuitState",
    "DistributedResilienceService",
    "FallbackChain",
    "FallbackLevel",
    "HealthCheckConfig",
    "HealthChecker",
    "HealthCheckResult",
    "HealthCheckType",
    "IdempotencyKey",
    "LatencyMetrics",
    "LeakyBucket",
    "PriorityLevel",
    "RateLimitConfig",
    "RetryAttempt",
    "RetryBudget",
    "RetryBudgetExhaustedError",
    "RetryConfig",
    "RetryManager",
    "RetryStrategy",
    "RetryableError",
    "SlidingWindowCounter",
    "TimeoutConfig",
    "TokenBucket",
    "get_resilience_service",
    "resilient",
]
