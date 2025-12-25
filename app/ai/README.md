# LLM Client Architecture

## Overview

This module implements a production-grade LLM client with advanced features including circuit breaking, cost management, intelligent retries, caching, and comprehensive observability.

## Architecture

```
app/ai/
├── facade.py                    # Backward-compatible facade
├── domain/
│   └── ports/                   # Interface definitions (Protocols)
├── application/                 # Business logic layer
│   ├── circuit_breaker.py       # Failure protection
│   ├── cost_manager.py          # Budget tracking
│   ├── retry_strategy.py        # Intelligent retries
│   ├── payload_builder.py       # Request construction
│   └── response_normalizer.py   # Response processing
├── infrastructure/              # External integrations
│   └── transports/              # Provider implementations
│       ├── openai_transport.py
│       ├── anthropic_transport.py
│       └── openrouter_transport.py
├── observability/               # Monitoring & tracing
└── optimization/                # Performance optimization
```

## Design Patterns

### Hexagonal Architecture (Ports & Adapters)

The system follows hexagonal architecture with clear separation:

- **Domain Layer**: Core business logic and interfaces
- **Application Layer**: Use cases and orchestration
- **Infrastructure Layer**: External service adapters

### Facade Pattern

`facade.py` provides backward compatibility while delegating to specialized components:

```python
from app.ai.facade import get_llm_client_service

client = get_llm_client_service()
response = client.invoke_chat(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Strategy Pattern

Multiple retry strategies available:

```python
from app.ai.application.retry_strategy import (
    ExponentialBackoffRetry,
    LinearBackoffRetry,
    FibonacciBackoffRetry,
    AdaptiveRetry,
)

# Use adaptive retry that learns from errors
strategy = AdaptiveRetry()
```

### Circuit Breaker Pattern

Protects against cascading failures:

```python
from app.ai.application.circuit_breaker import CircuitBreaker

breaker = CircuitBreaker("llm_service")
result = breaker.call(lambda: expensive_operation())
```

## Key Features

### 1. Circuit Breaker

**Purpose**: Prevent cascading failures and allow system recovery

**States**:
- `CLOSED`: Normal operation
- `OPEN`: Failing, rejecting requests
- `HALF_OPEN`: Testing recovery

**Features**:
- Adaptive failure thresholds
- Exponential backoff with jitter
- Automatic recovery testing
- Metrics collection

**Usage**:
```python
from app.ai.application.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
)

config = CircuitBreakerConfig(
    failure_threshold=5,
    success_threshold=2,
    timeout=60.0,
)

breaker = CircuitBreaker("my_service", config)

try:
    result = breaker.call(my_function, arg1, arg2)
except CircuitBreakerOpenError:
    # Handle circuit open
    pass
```

### 2. Cost Management

**Purpose**: Track and enforce budget limits

**Features**:
- Real-time cost tracking per model/user/project
- Budget enforcement with soft/hard limits
- Cost prediction and forecasting
- Optimization recommendations
- Multi-tier pricing support

**Usage**:
```python
from app.ai.application.cost_manager import (
    get_cost_manager,
    BudgetConfig,
    BudgetPeriod,
)

manager = get_cost_manager()

# Set budget
manager.set_budget(
    "daily_budget",
    BudgetConfig(limit=100.0, period=BudgetPeriod.DAILY)
)

# Track usage
record = manager.track_usage(
    model="gpt-4",
    input_tokens=1000,
    output_tokens=500,
    user_id="user123",
)

# Get metrics
metrics = manager.get_metrics()
print(f"Total cost: ${metrics.total_cost:.2f}")

# Get recommendations
recommendations = manager.get_optimization_recommendations()
```

### 3. Retry Strategy

**Purpose**: Handle transient failures intelligently

**Strategies**:
- **Exponential Backoff**: Delay increases exponentially
- **Linear Backoff**: Delay increases linearly
- **Fibonacci Backoff**: Follows Fibonacci sequence
- **Adaptive**: Learns from error patterns

**Features**:
- Error classification
- Jitter to prevent thundering herd
- Per-error-type retry policies
- Metrics collection

**Usage**:
```python
from app.ai.application.retry_strategy import (
    ExponentialBackoffRetry,
    RetryConfig,
    RetryExecutor,
)

config = RetryConfig(
    max_attempts=5,
    base_delay=1.0,
    exponential_base=2.0,
)

strategy = ExponentialBackoffRetry(config)
executor = RetryExecutor(strategy)

result = executor.execute(my_function, arg1, arg2)
```

### 4. Observability

**Purpose**: Monitor and trace LLM operations

**Features**:
- Distributed tracing with spans
- Metrics collection (counters, gauges, histograms)
- Performance monitoring
- Error tracking
- Real-time dashboards

**Usage**:
```python
from app.ai.observability import get_observability

obs = get_observability()

# Start tracing
span = obs.trace_operation("llm_call", model="gpt-4")

try:
    result = perform_operation()
    obs.finish_operation(span, status="success")
except Exception as e:
    obs.finish_operation(span, status="error", error=str(e))
    raise

# Get metrics
dashboard = obs.get_dashboard_data()
```

### 5. Performance Optimization

**Purpose**: Reduce latency and costs

**Features**:
- Semantic caching with TTL
- Request batching
- Response deduplication
- Prompt optimization
- Token usage optimization

**Usage**:
```python
from app.ai.optimization import (
    get_cache,
    PromptOptimizer,
    get_deduplicator,
)

# Caching
cache = get_cache()
cached_response = cache.get(request_key)
if not cached_response:
    response = call_llm()
    cache.set(request_key, response, ttl=3600)

# Prompt optimization
optimizer = PromptOptimizer()
optimized = optimizer.optimize(
    text=long_prompt,
    max_tokens=1000,
    remove_redundancy=True,
)

# Deduplication
dedup = get_deduplicator()
result = dedup.deduplicate(
    key=request_hash,
    executor=lambda: expensive_call()
)
```

## Transport Implementations

### OpenRouter

Default transport using OpenRouter API:

```python
from app.ai.infrastructure.transports import OpenRouterTransport

transport = OpenRouterTransport(client)
response = transport.chat_completion(
    messages=[{"role": "user", "content": "Hello"}],
    model="openai/gpt-4",
)
```

### OpenAI

Direct OpenAI API integration:

```python
from app.ai.infrastructure.transports.openai_transport import OpenAITransport

transport = OpenAITransport(api_key="sk-...")
response = transport.chat_completion(
    messages=[{"role": "user", "content": "Hello"}],
    model="gpt-4",
)
```

### Anthropic

Claude models support:

```python
from app.ai.infrastructure.transports.anthropic_transport import AnthropicTransport

transport = AnthropicTransport(api_key="sk-ant-...")
response = transport.chat_completion(
    messages=[{"role": "user", "content": "Hello"}],
    model="claude-3-opus-20240229",
)
```

### Mock

Testing transport:

```python
from app.ai.infrastructure.transports import MockLLMTransport

transport = MockLLMTransport(default_response="Test response")
response = transport.chat_completion(
    messages=[{"role": "user", "content": "Hello"}],
    model="mock-model",
)
```

## Configuration

### Environment Variables

```bash
# Provider selection
LLM_PROVIDER=openrouter  # openrouter, openai, anthropic, mock
LLM_FORCE_MOCK=0         # Force mock mode

# Budget limits
LLM_DAILY_BUDGET=100.0
LLM_MONTHLY_BUDGET=3000.0

# Circuit breaker
LLM_CIRCUIT_FAILURE_THRESHOLD=5
LLM_CIRCUIT_TIMEOUT=60

# Retry configuration
LLM_MAX_RETRIES=3
LLM_RETRY_BACKOFF_BASE=2.0

# Caching
LLM_CACHE_ENABLED=1
LLM_CACHE_TTL=3600
```

### Programmatic Configuration

```python
from app.ai.facade import LLMClientService
from app.ai.application.circuit_breaker import CircuitBreakerConfig
from app.ai.application.retry_strategy import RetryConfig

client = LLMClientService(
    provider="openai",
    circuit_breaker_config=CircuitBreakerConfig(
        failure_threshold=5,
        timeout=60.0,
    ),
    retry_config=RetryConfig(
        max_attempts=5,
        base_delay=1.0,
    ),
)
```

## Testing

### Unit Tests

```bash
pytest tests/ai/test_circuit_breaker.py
pytest tests/ai/test_cost_manager.py
pytest tests/ai/test_retry_strategy.py
```

### Integration Tests

```bash
pytest tests/ai/test_llm_client_integration.py
```

### Mock Testing

```python
from app.ai.infrastructure.transports import MockLLMTransport

transport = MockLLMTransport("Mock response")
# Use in tests
```

## Metrics & Monitoring

### Available Metrics

**Circuit Breaker**:
- `circuit.state` - Current state (closed/open/half_open)
- `circuit.requests.total` - Total requests
- `circuit.requests.successful` - Successful requests
- `circuit.requests.failed` - Failed requests
- `circuit.requests.rejected` - Rejected requests

**Cost Management**:
- `cost.total` - Total cost
- `cost.by_model` - Cost per model
- `cost.by_user` - Cost per user
- `cost.requests` - Total requests

**Retry Strategy**:
- `retry.attempts` - Total retry attempts
- `retry.successful` - Successful retries
- `retry.failed` - Failed retries
- `retry.delay` - Total delay time

### Dashboard Example

```python
from app.ai.facade import get_llm_client_service

client = get_llm_client_service()

# Get all metrics
cost_metrics = client.get_cost_metrics()
circuit_status = client.get_circuit_breaker_status()
retry_metrics = client.get_retry_metrics()

print(f"Total cost: ${cost_metrics['total_cost']:.2f}")
print(f"Circuit state: {circuit_status['state']}")
print(f"Retry success rate: {retry_metrics['successful_retries']}")
```

## Best Practices

### 1. Always Use Circuit Breaker

Wrap external calls in circuit breaker to prevent cascading failures:

```python
breaker = get_circuit_breaker("external_service")
result = breaker.call(external_api_call)
```

### 2. Set Appropriate Budgets

Configure budgets to prevent cost overruns:

```python
manager = get_cost_manager()
manager.set_budget("daily", BudgetConfig(limit=100.0, period=BudgetPeriod.DAILY))
```

### 3. Use Adaptive Retry

Adaptive retry learns from error patterns:

```python
strategy = AdaptiveRetry()
executor = RetryExecutor(strategy)
```

### 4. Enable Caching

Cache responses to reduce costs and latency:

```python
cache = get_cache()
response = cache.get(key) or call_llm_and_cache(key)
```

### 5. Monitor Metrics

Regularly check metrics for optimization opportunities:

```python
recommendations = cost_manager.get_optimization_recommendations()
for rec in recommendations:
    print(rec)
```

## Migration Guide

### From Old LLM Client

**Before**:
```python
from app.services.llm_client import invoke_chat

response = invoke_chat(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}],
)
```

**After**:
```python
from app.ai.facade import invoke_chat

response = invoke_chat(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}],
)
```

The facade maintains 100% backward compatibility.

## Performance Characteristics

### Latency

- **Without caching**: ~500-2000ms (depends on model)
- **With caching**: ~1-5ms (cache hit)
- **Circuit breaker overhead**: <1ms
- **Retry overhead**: Depends on backoff strategy

### Throughput

- **Single request**: 1-2 requests/second
- **With batching**: 10-50 requests/second
- **With caching**: 1000+ requests/second (cache hits)

### Memory Usage

- **Base**: ~10MB
- **With cache (1000 entries)**: ~50MB
- **With observability**: ~20MB

## Troubleshooting

### Circuit Breaker Stuck Open

```python
# Manually reset
breaker.reset()

# Or adjust thresholds
config = CircuitBreakerConfig(failure_threshold=10)
```

### Budget Exceeded

```python
# Check status
status = manager.get_budget_status("daily")
print(f"Usage: {status['percentage']}%")

# Increase limit
manager.set_budget("daily", BudgetConfig(limit=200.0))
```

### High Latency

```python
# Enable caching
cache = get_cache()

# Use prompt optimization
optimizer = PromptOptimizer()
optimized = optimizer.optimize(prompt, max_tokens=1000)

# Check metrics
metrics = obs.get_dashboard_data()
print(f"Avg duration: {metrics['avg_duration_ms']}ms")
```

## Contributing

When adding new features:

1. Follow hexagonal architecture
2. Add comprehensive tests
3. Update documentation
4. Add metrics/observability
5. Consider backward compatibility

## License

Internal use only.
