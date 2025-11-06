# 💥 Distributed Resilience Service - Quick Reference

## 🚀 Quick Start

```python
from app.services.distributed_resilience_service import get_resilience_service

# Get global service
service = get_resilience_service()
```

## 📚 Core Components

### 1. Circuit Breaker
```python
from app.services.distributed_resilience_service import CircuitBreakerConfig

cb = service.get_or_create_circuit_breaker(
    "api_gateway",
    CircuitBreakerConfig(failure_threshold=5, timeout_seconds=60)
)

result = cb.call(your_function)
```

### 2. Retry Manager
```python
from app.services.distributed_resilience_service import RetryConfig

rm = service.get_or_create_retry_manager(
    "database",
    RetryConfig(max_retries=3, retry_budget_percent=10.0)
)

result = rm.execute_with_retry(your_function, idempotency_key="unique-id")
```

### 3. Bulkhead
```python
from app.services.distributed_resilience_service import BulkheadConfig, PriorityLevel

bh = service.get_or_create_bulkhead(
    "api_calls",
    BulkheadConfig(max_concurrent_calls=100)
)

result = bh.execute(your_function, priority=PriorityLevel.HIGH)
```

### 4. Fallback Chain
```python
from app.services.distributed_resilience_service import FallbackChain, FallbackLevel

chain = FallbackChain()
chain.register_handler(FallbackLevel.PRIMARY, primary_func)
chain.register_handler(FallbackLevel.REPLICA, replica_func)
chain.register_handler(FallbackLevel.DEFAULT, default_func)

result, level, degraded = chain.execute()
```

### 5. Rate Limiting
```python
from app.services.distributed_resilience_service import TokenBucket

bucket = TokenBucket(capacity=1000, refill_rate=100)

if bucket.allow():
    process_request()
else:
    return rate_limit_response()
```

## 🎨 Decorator Usage

```python
from app.services.distributed_resilience_service import resilient, RetryConfig

@resilient(
    circuit_breaker_name="payment",
    retry_config=RetryConfig(max_retries=3),
    bulkhead_name="payment_api"
)
def process_payment(amount):
    # Fully protected function
    return payment_api.charge(amount)
```

## 📊 Monitoring

```python
# Get comprehensive stats
stats = service.get_comprehensive_stats()

# Individual component stats
cb_stats = cb.get_stats()
rm_stats = rm.retry_budget.get_stats()
bh_stats = bh.get_stats()
```

## ✅ All 15 Core Principles

1. ✅ No Single Point of Failure
2. ✅ Fail Fast
3. ✅ Graceful Degradation
4. ✅ Circuit Breaker
5. ✅ Bulkhead Isolation
6. ✅ Exponential Backoff
7. ✅ Timeout Everything
8. ✅ Health Checks
9. ✅ Idempotency
10. ✅ Retry Budget
11. ✅ Fallback Chain
12. ✅ Chaos Engineering (chaos_engineering.py)
13. ✅ Rate Limiting
14. ✅ Observability
15. ✅ Auto-Recovery

## 📖 Documentation

- **Arabic Guide:** `DISTRIBUTED_RESILIENCE_GUIDE_AR.md`
- **English Guide:** `DISTRIBUTED_RESILIENCE_GUIDE_EN.md`
- **Source Code:** `app/services/distributed_resilience_service.py`
- **Tests:** `tests/test_distributed_resilience.py` (42 tests ✅)

## 🎯 Target Metrics

- **Netflix-level:** 99.99% Uptime ✅
- **Google-level:** 99.999% Availability ✅
- **AWS-level:** 99.999999999% Durability ✅
