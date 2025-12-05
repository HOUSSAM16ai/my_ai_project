import pytest
from unittest.mock import Mock, patch
from app.services.resilience.service import DistributedResilienceService, get_resilience_service, resilient
from app.services.resilience.circuit_breaker import CircuitBreakerConfig, CircuitState, CircuitBreakerOpenError
from app.services.resilience.retry import RetryConfig, RetryStrategy, RetryBudgetExhaustedError

class TestDistributedResilienceService:
    @pytest.fixture
    def service(self):
        # Create fresh instance
        return DistributedResilienceService()

    def test_get_or_create_circuit_breaker(self, service):
        """Test getting or creating circuit breaker"""
        config = CircuitBreakerConfig(failure_threshold=5)
        cb1 = service.get_or_create_circuit_breaker("test-service", config)

        # Should return same instance
        cb2 = service.get_or_create_circuit_breaker("test-service")
        assert cb1 is cb2
        assert cb1.name == "test-service"
        assert cb1.config.failure_threshold == 5

        # Stats should appear
        stats = service.get_comprehensive_stats()
        assert "test-service" in stats["circuit_breakers"]

    def test_get_or_create_retry_manager(self, service):
        """Test getting or creating retry manager"""
        config = RetryConfig(max_retries=2)
        rm1 = service.get_or_create_retry_manager("test-retry", config)

        rm2 = service.get_or_create_retry_manager("test-retry")
        assert rm1 is rm2
        assert rm1.config.max_retries == 2

        stats = service.get_comprehensive_stats()
        assert "test-retry" in stats["retry_managers"]

    def test_singleton_accessor(self):
        """Test get_resilience_service returns singleton"""
        s1 = get_resilience_service()
        s2 = get_resilience_service()
        assert s1 is s2
        assert isinstance(s1, DistributedResilienceService)

    def test_resilient_decorator_circuit_breaker(self):
        """Test resilient decorator with circuit breaker"""

        # Reset global instance to ensure clean state
        global _resilience_service
        # We can't easily reset the global variable from here without access to module
        # But we can verify it uses a service.

        @resilient(circuit_breaker_name="test-decorator-cb")
        def success_func():
            return "success"

        result = success_func()
        assert result == "success"

        # Verify it created a CB in the global service
        service = get_resilience_service()
        assert "test-decorator-cb" in service.circuit_breakers

        # Test failure
        @resilient(circuit_breaker_name="test-decorator-cb-fail")
        def fail_func():
            raise ValueError("fail")

        with pytest.raises(ValueError):
            fail_func()

        cb = service.circuit_breakers["test-decorator-cb-fail"]
        assert cb.state.failure_count == 1

    def test_resilient_decorator_retry(self):
        """Test resilient decorator with retry"""
        mock_func = Mock(side_effect=[ValueError("fail"), "success"])

        @resilient(retry_config=RetryConfig(max_retries=2, base_delay_ms=1))
        def retry_func():
            return mock_func()

        result = retry_func()
        assert result == "success"
        assert mock_func.call_count == 2
