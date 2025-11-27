# tests/test_distributed_resilience.py
# ======================================================================================
# ==    COMPREHENSIVE TESTS FOR DISTRIBUTED RESILIENCE SERVICE                       ==
# ======================================================================================

import time
from unittest.mock import Mock

import pytest

from app.services.distributed_resilience_service import (AdaptiveTimeout, Bulkhead, BulkheadConfig,
                                                         BulkheadFullError, CircuitBreaker,
                                                         CircuitBreakerConfig,
                                                         CircuitBreakerOpenError, CircuitState,
                                                         DistributedResilienceService,
                                                         FallbackChain, FallbackLevel,
                                                         HealthCheckConfig, HealthChecker,
                                                         HealthCheckType, LeakyBucket, RetryBudget,
                                                         RetryBudgetExhaustedError, RetryConfig,
                                                         RetryManager, RetryStrategy,
                                                         SlidingWindowCounter, TimeoutConfig,
                                                         TokenBucket, get_resilience_service,
                                                         resilient)

# ======================================================================================
# CIRCUIT BREAKER TESTS
# ======================================================================================


class TestCircuitBreaker:
    """Test Circuit Breaker Pattern"""

    def test_circuit_starts_closed(self):
        """Circuit should start in CLOSED state"""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test", config)
        assert cb.state.state == CircuitState.CLOSED

    def test_circuit_opens_after_threshold(self):
        """Circuit should open after failure threshold"""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker("test", config)

        def failing_func():
            raise Exception("Test error")

        # Fail 3 times
        for _ in range(3):
            with pytest.raises(Exception):  # noqa: B017
                cb.call(failing_func)

        assert cb.state.state == CircuitState.OPEN

    def test_circuit_rejects_when_open(self):
        """Circuit should reject calls when OPEN"""
        config = CircuitBreakerConfig(failure_threshold=1, timeout_seconds=60)
        cb = CircuitBreaker("test", config)

        def failing_func():
            raise Exception("Test error")

        # Open the circuit
        with pytest.raises(Exception):  # noqa: B017
            cb.call(failing_func)

        # Should reject immediately
        with pytest.raises(CircuitBreakerOpenError):
            cb.call(lambda: "success")

    def test_circuit_transitions_to_half_open(self):
        """Circuit should transition to HALF_OPEN after timeout"""
        config = CircuitBreakerConfig(failure_threshold=1, timeout_seconds=1)
        cb = CircuitBreaker("test", config)

        def failing_func():
            raise Exception("Test error")

        # Open the circuit
        with pytest.raises(Exception):  # noqa: B017
            cb.call(failing_func)

        assert cb.state.state == CircuitState.OPEN

        # Wait for timeout
        time.sleep(1.1)

        # Should allow test calls in HALF_OPEN
        assert cb._get_state() == CircuitState.HALF_OPEN

    def test_circuit_closes_after_success_in_half_open(self):
        """Circuit should close after success threshold in HALF_OPEN"""
        config = CircuitBreakerConfig(failure_threshold=1, success_threshold=2, timeout_seconds=1)
        cb = CircuitBreaker("test", config)

        def failing_func():
            raise Exception("Test error")

        def success_func():
            return "success"

        # Open the circuit
        with pytest.raises(Exception):  # noqa: B017
            cb.call(failing_func)

        # Wait for HALF_OPEN
        time.sleep(1.1)

        # Succeed twice
        cb.call(success_func)
        cb.call(success_func)

        assert cb.state.state == CircuitState.CLOSED

    def test_circuit_stats(self):
        """Circuit breaker should provide stats"""
        config = CircuitBreakerConfig()
        cb = CircuitBreaker("test", config)

        stats = cb.get_stats()
        assert stats["name"] == "test"
        assert stats["state"] == "closed"
        assert "failure_count" in stats
        assert "success_count" in stats


# ======================================================================================
# RETRY MANAGER TESTS
# ======================================================================================


class TestRetryManager:
    """Test Retry Manager with Exponential Backoff"""

    def test_retry_on_failure(self):
        """Should retry on failure"""
        config = RetryConfig(max_retries=3, base_delay_ms=10)
        rm = RetryManager(config)

        call_count = 0

        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Flaky error")
            return "success"

        result = rm.execute_with_retry(flaky_func)
        assert result == "success"
        assert call_count == 3

    def test_exponential_backoff_delay(self):
        """Should use exponential backoff"""
        config = RetryConfig(
            max_retries=3, base_delay_ms=100, strategy=RetryStrategy.EXPONENTIAL_BACKOFF
        )
        rm = RetryManager(config)

        # Test multiple times to account for jitter
        delays_list = []
        for _ in range(10):
            delays = []
            for i in range(3):
                delay = rm._calculate_delay(i)
                delays.append(delay)
            delays_list.append(delays)

        # On average, delays should increase exponentially
        avg_delays = [sum(d[i] for d in delays_list) / len(delays_list) for i in range(3)]
        assert avg_delays[1] > avg_delays[0]
        assert avg_delays[2] > avg_delays[1]

    def test_idempotency_cache(self):
        """Should cache results for idempotent operations"""
        config = RetryConfig()
        rm = RetryManager(config)

        call_count = 0

        def counted_func():
            nonlocal call_count
            call_count += 1
            return f"result_{call_count}"

        # First call
        result1 = rm.execute_with_retry(counted_func, idempotency_key="test_key")
        assert call_count == 1

        # Second call should return cached
        result2 = rm.execute_with_retry(counted_func, idempotency_key="test_key")
        assert call_count == 1  # Not incremented
        assert result1 == result2

    def test_retry_budget_exhaustion(self):
        """Should fail fast when retry budget exhausted"""
        config = RetryConfig(retry_budget_percent=1.0)
        rm = RetryManager(config)

        # Exhaust budget
        for _ in range(100):
            rm.retry_budget.track_retry()

        # Should fail fast
        with pytest.raises(RetryBudgetExhaustedError):
            rm.execute_with_retry(lambda: None)

    def test_no_retry_on_4xx_errors(self):
        """Should not retry on 4xx errors"""
        config = RetryConfig(max_retries=3)
        rm = RetryManager(config)

        call_count = 0

        def func_with_status():
            nonlocal call_count
            call_count += 1
            # Simulate HTTP response
            response = Mock()
            response.status_code = 404
            return response

        _ = rm.execute_with_retry(func_with_status)
        assert call_count == 1  # No retry on 4xx


class TestRetryBudget:
    """Test Retry Budget"""

    def test_budget_allows_initial_retries(self):
        """Budget should allow retries initially"""
        budget = RetryBudget(budget_percent=10.0)
        assert budget.can_retry() is True

    def test_budget_blocks_excessive_retries(self):
        """Budget should block when limit exceeded"""
        budget = RetryBudget(budget_percent=10.0)

        # Track many retries
        for _ in range(200):
            budget.track_retry()

        assert budget.can_retry() is False

    def test_budget_stats(self):
        """Budget should provide stats"""
        budget = RetryBudget(budget_percent=10.0)

        for _ in range(10):
            budget.track_retry()

        stats = budget.get_stats()
        assert "total_requests" in stats
        assert "total_retries" in stats
        assert "retry_rate_percent" in stats


# ======================================================================================
# BULKHEAD TESTS
# ======================================================================================


class TestBulkhead:
    """Test Bulkhead Pattern"""

    def test_bulkhead_limits_concurrency(self):
        """Bulkhead should limit concurrent calls"""
        config = BulkheadConfig(max_concurrent_calls=2)
        bulkhead = Bulkhead("test", config)

        results = []

        def slow_func():
            time.sleep(0.1)
            return "done"

        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(bulkhead.execute, slow_func) for _ in range(5)]

            for future in concurrent.futures.as_completed(futures):
                try:
                    results.append(future.result())
                except BulkheadFullError:
                    results.append("rejected")

        # Some should be rejected
        assert "rejected" in results

    def test_bulkhead_stats(self):
        """Bulkhead should provide stats"""
        config = BulkheadConfig(max_concurrent_calls=10)
        bulkhead = Bulkhead("test", config)

        stats = bulkhead.get_stats()
        assert stats["name"] == "test"
        assert stats["max_concurrent"] == 10
        assert "active_calls" in stats
        assert "utilization_percent" in stats


# ======================================================================================
# ADAPTIVE TIMEOUT TESTS
# ======================================================================================


class TestAdaptiveTimeout:
    """Test Adaptive Timeout"""

    def test_records_latency(self):
        """Should record latency samples"""
        config = TimeoutConfig(adaptive_enabled=True)
        timeout = AdaptiveTimeout(config)

        timeout.record_latency(100.0)
        timeout.record_latency(150.0)
        timeout.record_latency(200.0)

        assert len(timeout.metrics.samples) == 3

    def test_calculates_percentiles(self):
        """Should calculate percentiles"""
        config = TimeoutConfig(adaptive_enabled=True)
        timeout = AdaptiveTimeout(config)

        # Add many samples
        for i in range(1000):
            timeout.record_latency(float(i))

        stats = timeout.get_stats()
        assert stats["p50"] > 0
        assert stats["p95"] > stats["p50"]
        assert stats["p99"] > stats["p95"]

    def test_adaptive_timeout_based_on_p95(self):
        """Timeout should adapt based on P95"""
        config = TimeoutConfig(adaptive_enabled=True, request_timeout_ms=10000)
        timeout = AdaptiveTimeout(config)

        # Record fast responses
        for _ in range(100):
            timeout.record_latency(100.0)

        adaptive = timeout.get_timeout_ms()
        # Should be around P95 * 1.5 = 100 * 1.5 = 150ms
        assert adaptive < config.request_timeout_ms


# ======================================================================================
# FALLBACK CHAIN TESTS
# ======================================================================================


class TestFallbackChain:
    """Test Fallback Chain"""

    def test_uses_primary_when_available(self):
        """Should use primary source when available"""
        chain = FallbackChain()

        chain.register_handler(FallbackLevel.PRIMARY, lambda: "primary")
        chain.register_handler(FallbackLevel.REPLICA, lambda: "replica")

        result, level, degraded = chain.execute()
        assert result == "primary"
        assert level == FallbackLevel.PRIMARY
        assert degraded is False

    def test_falls_back_on_failure(self):
        """Should fallback to next level on failure"""
        chain = FallbackChain()

        def failing_primary():
            raise Exception("Primary failed")

        chain.register_handler(FallbackLevel.PRIMARY, failing_primary)
        chain.register_handler(FallbackLevel.REPLICA, lambda: "replica")

        result, level, degraded = chain.execute()
        assert result == "replica"
        assert level == FallbackLevel.REPLICA
        assert degraded is True

    def test_multi_level_fallback(self):
        """Should try multiple levels"""
        chain = FallbackChain()

        def fail():
            raise Exception("Failed")

        chain.register_handler(FallbackLevel.PRIMARY, fail)
        chain.register_handler(FallbackLevel.REPLICA, fail)
        chain.register_handler(FallbackLevel.DISTRIBUTED_CACHE, fail)
        chain.register_handler(FallbackLevel.DEFAULT, lambda: "default")

        result, level, _degraded = chain.execute()
        assert result == "default"
        assert level == FallbackLevel.DEFAULT


# ======================================================================================
# RATE LIMITING TESTS
# ======================================================================================


class TestTokenBucket:
    """Test Token Bucket Algorithm"""

    def test_allows_within_capacity(self):
        """Should allow requests within capacity"""
        bucket = TokenBucket(capacity=10, refill_rate=1)

        for _ in range(10):
            assert bucket.allow() is True

    def test_rejects_over_capacity(self):
        """Should reject when capacity exceeded"""
        bucket = TokenBucket(capacity=5, refill_rate=0)

        # Use all tokens
        for _ in range(5):
            bucket.allow()

        # Should reject
        assert bucket.allow() is False

    def test_refills_tokens(self):
        """Should refill tokens over time"""
        bucket = TokenBucket(capacity=10, refill_rate=10)

        # Use all tokens
        for _ in range(10):
            bucket.allow()

        # Wait for refill
        time.sleep(1.1)

        # Should allow again
        assert bucket.allow() is True


class TestSlidingWindowCounter:
    """Test Sliding Window Algorithm"""

    def test_allows_within_limit(self):
        """Should allow requests within limit"""
        counter = SlidingWindowCounter(limit=5, window_seconds=1)

        for _ in range(5):
            assert counter.allow() is True

    def test_rejects_over_limit(self):
        """Should reject when limit exceeded"""
        counter = SlidingWindowCounter(limit=3, window_seconds=1)

        for _ in range(3):
            counter.allow()

        assert counter.allow() is False

    def test_window_slides(self):
        """Window should slide with time"""
        counter = SlidingWindowCounter(limit=3, window_seconds=1)

        # Fill window
        for _ in range(3):
            counter.allow()

        # Wait for window to slide
        time.sleep(1.1)

        # Should allow again
        assert counter.allow() is True


class TestLeakyBucket:
    """Test Leaky Bucket Algorithm"""

    def test_allows_within_capacity(self):
        """Should allow requests within capacity"""
        bucket = LeakyBucket(capacity=5, leak_rate=1)

        for _ in range(5):
            assert bucket.allow() is True

    def test_rejects_over_capacity(self):
        """Should reject when capacity exceeded"""
        bucket = LeakyBucket(capacity=3, leak_rate=0)

        for _ in range(3):
            bucket.allow()

        assert bucket.allow() is False

    def test_leaks_over_time(self):
        """Should leak requests over time"""
        bucket = LeakyBucket(capacity=5, leak_rate=5)

        # Fill bucket
        for _ in range(5):
            bucket.allow()

        # Wait for leak
        time.sleep(1.1)

        # Should allow again
        assert bucket.allow() is True


# ======================================================================================
# HEALTH CHECK TESTS
# ======================================================================================


class TestHealthChecker:
    """Test Health Check System"""

    def test_healthy_check(self):
        """Should report healthy on success"""
        config = HealthCheckConfig(check_type=HealthCheckType.LIVENESS)
        checker = HealthChecker(config)

        def healthy_func():
            return {"status": "ok"}

        result = checker.check(healthy_func)
        assert result.healthy is True
        assert result.check_type == HealthCheckType.LIVENESS

    def test_unhealthy_check(self):
        """Should report unhealthy on failure"""
        config = HealthCheckConfig(check_type=HealthCheckType.READINESS)
        checker = HealthChecker(config)

        def unhealthy_func():
            raise Exception("Service down")

        result = checker.check(unhealthy_func)
        assert result.healthy is False
        assert result.error is not None

    def test_grace_period(self):
        """Should use grace period before marking unhealthy"""
        config = HealthCheckConfig(grace_period_failures=3)
        checker = HealthChecker(config)

        def failing_func():
            raise Exception("Failed")

        # Fail once - still healthy
        checker.check(failing_func)
        assert checker.is_healthy() is True

        # Fail twice - still healthy
        checker.check(failing_func)
        assert checker.is_healthy() is True

        # Fail third time - now unhealthy
        checker.check(failing_func)
        assert checker.is_healthy() is False


# ======================================================================================
# RESILIENCE SERVICE TESTS
# ======================================================================================


class TestDistributedResilienceService:
    """Test Comprehensive Resilience Service"""

    def test_creates_circuit_breakers(self):
        """Should create and reuse circuit breakers"""
        service = DistributedResilienceService()

        cb1 = service.get_or_create_circuit_breaker("test")
        cb2 = service.get_or_create_circuit_breaker("test")

        assert cb1 is cb2

    def test_creates_retry_managers(self):
        """Should create and reuse retry managers"""
        service = DistributedResilienceService()

        rm1 = service.get_or_create_retry_manager("test")
        rm2 = service.get_or_create_retry_manager("test")

        assert rm1 is rm2

    def test_creates_bulkheads(self):
        """Should create and reuse bulkheads"""
        service = DistributedResilienceService()

        bh1 = service.get_or_create_bulkhead("test")
        bh2 = service.get_or_create_bulkhead("test")

        assert bh1 is bh2

    def test_comprehensive_stats(self):
        """Should provide comprehensive stats"""
        service = DistributedResilienceService()

        # Create some components
        service.get_or_create_circuit_breaker("cb1")
        service.get_or_create_retry_manager("rm1")
        service.get_or_create_bulkhead("bh1")

        stats = service.get_comprehensive_stats()

        assert "circuit_breakers" in stats
        assert "retry_managers" in stats
        assert "bulkheads" in stats
        assert "cb1" in stats["circuit_breakers"]
        assert "rm1" in stats["retry_managers"]
        assert "bh1" in stats["bulkheads"]


# ======================================================================================
# DECORATOR TESTS
# ======================================================================================


class TestResilientDecorator:
    """Test Resilient Decorator"""

    def test_resilient_decorator_with_circuit_breaker(self):
        """Decorator should apply circuit breaker"""

        @resilient(circuit_breaker_name="test_cb")
        def protected_func():
            return "success"

        result = protected_func()
        assert result == "success"

    def test_resilient_decorator_with_retry(self):
        """Decorator should apply retry logic"""
        call_count = 0

        @resilient(retry_config=RetryConfig(max_retries=2, base_delay_ms=10))
        def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Exception("Flaky")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert call_count == 2


# ======================================================================================
# INTEGRATION TESTS
# ======================================================================================


class TestIntegration:
    """Integration tests combining multiple patterns"""

    def test_circuit_breaker_with_retry(self):
        """Circuit breaker and retry should work together"""
        service = DistributedResilienceService()

        cb = service.get_or_create_circuit_breaker(
            "integration", CircuitBreakerConfig(failure_threshold=5)
        )
        rm = service.get_or_create_retry_manager("integration", RetryConfig(max_retries=2))

        call_count = 0

        def semi_flaky():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Flaky")
            return "success"

        # Should retry and succeed
        result = cb.call(lambda: rm.execute_with_retry(semi_flaky))
        assert result == "success"

    def test_get_global_service(self):
        """Should provide global service instance"""
        service1 = get_resilience_service()
        service2 = get_resilience_service()

        assert service1 is service2
