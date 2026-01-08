"""
اختبارات قاطع الدائرة (Circuit Breaker Tests).

يختبر هذا الملف جميع وظائف قاطع الدائرة بما في ذلك:
- الحالات المختلفة (CLOSED, OPEN, HALF_OPEN)
- الانتقال بين الحالات
- معالجة الفشل والنجاح
- الإحصائيات
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from app.gateway.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitBreakerRegistry,
    CircuitState,
)


class TestCircuitBreakerConfig:
    """اختبارات تكوين قاطع الدائرة."""
    
    def test_default_config(self) -> None:
        """يختبر التكوين الافتراضي."""
        config = CircuitBreakerConfig()
        
        assert config.failure_threshold == 5
        assert config.success_threshold == 2
        assert config.timeout == 60
        assert config.half_open_max_calls == 3
    
    def test_custom_config(self) -> None:
        """يختبر تكوين مخصص."""
        config = CircuitBreakerConfig(
            failure_threshold=3,
            success_threshold=1,
            timeout=30,
            half_open_max_calls=2,
        )
        
        assert config.failure_threshold == 3
        assert config.success_threshold == 1
        assert config.timeout == 30
        assert config.half_open_max_calls == 2


class TestCircuitBreaker:
    """اختبارات قاطع الدائرة."""
    
    @pytest.mark.asyncio
    async def test_initial_state_closed(self) -> None:
        """يختبر أن الحالة الأولية مغلقة."""
        breaker = CircuitBreaker("test-service")
        
        assert breaker.stats.state == CircuitState.CLOSED
        assert breaker.stats.failure_count == 0
        assert breaker.stats.success_count == 0
    
    @pytest.mark.asyncio
    async def test_successful_call(self) -> None:
        """يختبر استدعاء ناجح."""
        breaker = CircuitBreaker("test-service")
        
        async def successful_func() -> str:
            return "success"
        
        result = await breaker.call(successful_func)
        
        assert result == "success"
        assert breaker.stats.total_calls == 1
        assert breaker.stats.total_successes == 1
        assert breaker.stats.total_failures == 0
    
    @pytest.mark.asyncio
    async def test_failed_call(self) -> None:
        """يختبر استدعاء فاشل."""
        breaker = CircuitBreaker("test-service")
        
        async def failing_func() -> None:
            raise ValueError("Test error")
        
        with pytest.raises(ValueError):
            await breaker.call(failing_func)
        
        assert breaker.stats.total_calls == 1
        assert breaker.stats.total_failures == 1
        assert breaker.stats.failure_count == 1
    
    @pytest.mark.asyncio
    async def test_transition_to_open(self) -> None:
        """يختبر الانتقال إلى حالة مفتوحة."""
        config = CircuitBreakerConfig(failure_threshold=3)
        breaker = CircuitBreaker("test-service", config)
        
        async def failing_func() -> None:
            raise ValueError("Test error")
        
        # فشل 3 مرات
        for _ in range(3):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)
        
        # يجب أن تكون الدائرة مفتوحة الآن
        assert breaker.stats.state == CircuitState.OPEN
    
    @pytest.mark.asyncio
    async def test_reject_when_open(self) -> None:
        """يختبر رفض الطلبات عند فتح الدائرة."""
        config = CircuitBreakerConfig(failure_threshold=2)
        breaker = CircuitBreaker("test-service", config)
        
        async def failing_func() -> None:
            raise ValueError("Test error")
        
        # فشل مرتين لفتح الدائرة
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)
        
        # محاولة استدعاء جديد يجب أن يُرفض
        async def any_func() -> str:
            return "should not execute"
        
        with pytest.raises(CircuitBreakerError) as exc_info:
            await breaker.call(any_func)
        
        assert exc_info.value.state == CircuitState.OPEN
    
    @pytest.mark.asyncio
    async def test_transition_to_half_open(self) -> None:
        """يختبر الانتقال إلى حالة نصف مفتوحة."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            timeout=1,  # ثانية واحدة فقط
        )
        breaker = CircuitBreaker("test-service", config)
        
        async def failing_func() -> None:
            raise ValueError("Test error")
        
        # فتح الدائرة
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)
        
        assert breaker.stats.state == CircuitState.OPEN
        
        # انتظار انتهاء المهلة
        await asyncio.sleep(1.1)
        
        # محاولة استدعاء جديد يجب أن ينقل إلى نصف مفتوحة
        async def successful_func() -> str:
            return "success"
        
        # التحقق من الحالة يدوياً
        await breaker._check_state()
        assert breaker.stats.state == CircuitState.HALF_OPEN
    
    @pytest.mark.asyncio
    async def test_transition_to_closed_from_half_open(self) -> None:
        """يختبر الانتقال إلى حالة مغلقة من نصف مفتوحة."""
        config = CircuitBreakerConfig(
            failure_threshold=2,
            success_threshold=2,
            timeout=1,
        )
        breaker = CircuitBreaker("test-service", config)
        
        async def failing_func() -> None:
            raise ValueError("Test error")
        
        async def successful_func() -> str:
            return "success"
        
        # فتح الدائرة
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)
        
        # انتظار وانتقال إلى نصف مفتوحة
        await asyncio.sleep(1.1)
        await breaker._check_state()
        
        # نجاح مرتين لإغلاق الدائرة
        for _ in range(2):
            await breaker.call(successful_func)
        
        assert breaker.stats.state == CircuitState.CLOSED
    
    @pytest.mark.asyncio
    async def test_get_stats(self) -> None:
        """يختبر الحصول على الإحصائيات."""
        breaker = CircuitBreaker("test-service")
        
        async def successful_func() -> str:
            return "success"
        
        await breaker.call(successful_func)
        
        stats = breaker.get_stats()
        
        assert stats["name"] == "test-service"
        assert stats["state"] == "closed"
        assert stats["total_calls"] == 1
        assert stats["total_successes"] == 1
        assert stats["failure_rate"] == 0.0
    
    @pytest.mark.asyncio
    async def test_reset(self) -> None:
        """يختبر إعادة تعيين القاطع."""
        config = CircuitBreakerConfig(failure_threshold=2)
        breaker = CircuitBreaker("test-service", config)
        
        async def failing_func() -> None:
            raise ValueError("Test error")
        
        # فتح الدائرة
        for _ in range(2):
            with pytest.raises(ValueError):
                await breaker.call(failing_func)
        
        assert breaker.stats.state == CircuitState.OPEN
        
        # إعادة التعيين
        await breaker.reset()
        
        assert breaker.stats.state == CircuitState.CLOSED
        assert breaker.stats.failure_count == 0
        assert breaker.stats.total_calls == 0


class TestCircuitBreakerRegistry:
    """اختبارات سجل قواطع الدائرة."""
    
    def test_registry_initialization(self) -> None:
        """يختبر تهيئة السجل."""
        registry = CircuitBreakerRegistry()
        
        assert registry is not None
        assert registry.default_config is not None
    
    def test_get_breaker(self) -> None:
        """يختبر الحصول على قاطع."""
        registry = CircuitBreakerRegistry()
        
        breaker1 = registry.get_breaker("service1")
        breaker2 = registry.get_breaker("service1")
        
        # يجب أن يعيد نفس المثيل
        assert breaker1 is breaker2
    
    def test_get_breaker_with_custom_config(self) -> None:
        """يختبر الحصول على قاطع بتكوين مخصص."""
        registry = CircuitBreakerRegistry()
        
        custom_config = CircuitBreakerConfig(failure_threshold=10)
        breaker = registry.get_breaker("service1", custom_config)
        
        assert breaker.config.failure_threshold == 10
    
    @pytest.mark.asyncio
    async def test_get_all_stats(self) -> None:
        """يختبر الحصول على إحصائيات جميع القواطع."""
        registry = CircuitBreakerRegistry()
        
        breaker1 = registry.get_breaker("service1")
        breaker2 = registry.get_breaker("service2")
        
        async def successful_func() -> str:
            return "success"
        
        await breaker1.call(successful_func)
        await breaker2.call(successful_func)
        
        all_stats = registry.get_all_stats()
        
        assert "service1" in all_stats
        assert "service2" in all_stats
        assert all_stats["service1"]["total_calls"] == 1
        assert all_stats["service2"]["total_calls"] == 1
    
    @pytest.mark.asyncio
    async def test_reset_all(self) -> None:
        """يختبر إعادة تعيين جميع القواطع."""
        registry = CircuitBreakerRegistry()
        
        breaker1 = registry.get_breaker("service1")
        breaker2 = registry.get_breaker("service2")
        
        async def successful_func() -> str:
            return "success"
        
        await breaker1.call(successful_func)
        await breaker2.call(successful_func)
        
        await registry.reset_all()
        
        all_stats = registry.get_all_stats()
        assert all_stats["service1"]["total_calls"] == 0
        assert all_stats["service2"]["total_calls"] == 0


class TestCircuitBreakerError:
    """اختبارات استثناء قاطع الدائرة."""
    
    def test_error_creation(self) -> None:
        """يختبر إنشاء الاستثناء."""
        error = CircuitBreakerError("test-service", CircuitState.OPEN)
        
        assert error.service_name == "test-service"
        assert error.state == CircuitState.OPEN
        assert "test-service" in str(error)
        assert "open" in str(error).lower()
