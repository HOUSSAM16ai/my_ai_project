# 🎯 API Gateway - Quick Start Guide

> **دليل البدء السريع لبوابة API**
>
> **Quick start guide for the superhuman API Gateway**

---

## 📋 Installation

The API Gateway is already integrated into the project. No additional installation required!

```bash
# Verify gateway services are available
python3 -m pytest tests/test_api_gateway.py -v
```

---

## 🚀 Basic Usage

### 1. Using the Intelligent Router

Route requests to the optimal AI provider based on cost, latency, or balanced criteria:

```python
from app.services.api_gateway_service import get_gateway_service, RoutingStrategy
from flask import current_app

# Get gateway instance
gateway = get_gateway_service()

# Route request intelligently
decision = gateway.intelligent_router.route_request(
    model_type="gpt-4",
    estimated_tokens=500,
    strategy=RoutingStrategy.INTELLIGENT,
    constraints={
        'max_cost': 0.05,
        'max_latency': 2000
    }
)

print(f"Selected provider: {decision.service_id}")
print(f"Estimated cost: ${decision.estimated_cost:.4f}")
print(f"Estimated latency: {decision.estimated_latency_ms}ms")
print(f"Confidence: {decision.confidence_score:.2f}")
```

**Output:**
```
Selected provider: openai
Estimated cost: $0.0010
Estimated latency: 750ms
Confidence: 0.85
```

---

### 2. Using Intelligent Caching

Cache expensive AI operations automatically:

```python
from app.services.api_gateway_service import get_gateway_service

gateway = get_gateway_service()

# Request data (cache key)
request_data = {
    'query': 'Explain quantum computing',
    'model': 'gpt-4',
    'temperature': 0.7
}

# Check cache first
cached_response = gateway.cache.get(request_data)
if cached_response:
    print("✅ Cache hit! Using cached response")
    result = cached_response
else:
    print("❌ Cache miss, calling API...")
    # Make expensive API call
    result = {'response': 'Quantum computing explanation...'}
    
    # Cache for 5 minutes
    gateway.cache.put(request_data, result, ttl_seconds=300)

# Get cache statistics
stats = gateway.cache.get_stats()
print(f"Cache hit rate: {stats['hit_rate']:.1%}")
print(f"Cached entries: {stats['entry_count']}")
```

---

### 3. Policy Enforcement

Enforce access control and compliance policies:

```python
from app.services.api_gateway_service import PolicyEngine, PolicyRule

engine = PolicyEngine()

# Add authentication policy
auth_policy = PolicyRule(
    rule_id="require_auth",
    name="Require Authentication",
    condition="auth_required and not authenticated",
    action="deny",
    priority=100,
    enabled=True
)
engine.add_policy(auth_policy)

# Evaluate request
request_context = {
    'authenticated': False,
    'endpoint': '/api/protected',
    'user_id': None
}

allowed, reason = engine.evaluate(request_context)
if not allowed:
    print(f"❌ Request denied: {reason}")
else:
    print("✅ Request allowed")
```

---

### 4. Chaos Engineering

Test system resilience with controlled fault injection:

```python
from app.services.api_gateway_chaos import (
    get_chaos_service,
    ChaosExperiment,
    FaultType
)

chaos = get_chaos_service()

# Create latency injection experiment
experiment = ChaosExperiment(
    experiment_id="latency_test_1",
    name="API Latency Test",
    description="Test system resilience to increased latency",
    fault_type=FaultType.LATENCY,
    target_service="openai",
    fault_rate=0.2,  # Inject fault in 20% of requests
    duration_seconds=300  # Run for 5 minutes
)

# Start experiment
if chaos.start_experiment(experiment):
    print("✅ Chaos experiment started")
    print(f"   Injecting {experiment.fault_type.value} faults")
    print(f"   Fault rate: {experiment.fault_rate * 100}%")
    print(f"   Duration: {experiment.duration_seconds}s")

# Later: stop experiment
chaos.stop_experiment("latency_test_1")
print("✅ Chaos experiment stopped")
```

---

### 5. Circuit Breaker Pattern

Protect against cascading failures:

```python
from app.services.api_gateway_chaos import (
    get_circuit_breaker,
    CircuitBreakerConfig
)

# Configure circuit breaker
config = CircuitBreakerConfig(
    failure_threshold=5,  # Open after 5 failures
    timeout_seconds=60,   # Stay open for 60 seconds
    half_open_requests=3  # Test with 3 requests before closing
)

cb = get_circuit_breaker()

# Call external service through circuit breaker
def call_external_api():
    # Your API call here
    import requests
    response = requests.get('https://api.example.com/data')
    return response.json()

success, result, error = cb.call("external_api", call_external_api)

if success:
    print(f"✅ API call successful: {result}")
else:
    print(f"❌ Call failed or circuit open: {error}")

# Check circuit state
state = cb.get_state("external_api")
print(f"Circuit breaker state: {state.value}")
```

---

### 6. A/B Testing

Compare two model versions or configurations:

```python
from app.services.api_gateway_deployment import (
    get_ab_testing_service,
    ABTestExperiment
)

ab_service = get_ab_testing_service()

# Create experiment
experiment = ABTestExperiment(
    experiment_id="model_comparison_1",
    name="GPT-4 vs GPT-3.5 Quality Test",
    description="Compare response quality",
    variant_a="gpt-4",
    variant_b="gpt-3.5-turbo",
    traffic_split=0.5  # 50/50 split
)

ab_service.create_experiment(experiment)
print("✅ A/B test created")

# Assign user to variant
user_id = "user_12345"
variant = ab_service.assign_variant("model_comparison_1", user_id)
print(f"User {user_id} assigned to: {variant}")

# Use assigned variant for request
if variant == "gpt-4":
    # Use GPT-4
    response = "High quality response..."
else:
    # Use GPT-3.5
    response = "Standard quality response..."

# Record outcome metrics
ab_service.record_outcome(
    "model_comparison_1",
    user_id,
    "satisfaction_score",
    0.92
)
ab_service.record_outcome(
    "model_comparison_1",
    user_id,
    "response_time_ms",
    850.0
)

# Get experiment results
results = ab_service.get_experiment_results("model_comparison_1")
print(f"Experiment results: {results}")
```

---

### 7. Canary Deployments

Gradually roll out new versions with automatic monitoring:

```python
from app.services.api_gateway_deployment import (
    get_canary_deployment_service,
    CanaryDeployment
)

canary_service = get_canary_deployment_service()

# Start canary deployment
deployment = CanaryDeployment(
    deployment_id="model_v2_rollout",
    service_id="ai_model_service",
    canary_version="v2.0",
    stable_version="v1.5",
    canary_traffic_percent=10.0,  # Start with 10%
    increment_percent=10.0,       # Increase by 10% each step
    increment_interval_minutes=15,
    success_threshold=0.95        # Require 95% success rate
)

canary_service.start_deployment(deployment)
print("✅ Canary deployment started at 10% traffic")

# For each request, get which version to use
user_id = "user_67890"
version = canary_service.get_version_for_request(
    "model_v2_rollout",
    user_id
)
print(f"Using version: {version}")

# After request completes, record outcome
canary_service.record_request_outcome(
    "model_v2_rollout",
    version,
    success=True,
    latency_ms=125.0
)

# Check if ready to increment traffic
if canary_service.should_increment_traffic("model_v2_rollout"):
    canary_service.increment_traffic("model_v2_rollout")
    print("✅ Traffic incremented to 20%")

# If problems detected, rollback
# canary_service.rollback("model_v2_rollout")
```

---

### 8. Feature Flags

Control feature availability at runtime:

```python
from app.services.api_gateway_deployment import (
    get_feature_flag_service,
    FeatureFlag,
    FeatureFlagStatus
)

flag_service = get_feature_flag_service()

# Create feature flag with 20% rollout
flag = FeatureFlag(
    flag_id="new_summarization_model",
    name="New Summarization Model",
    description="Enable improved summarization AI",
    status=FeatureFlagStatus.PERCENTAGE,
    enabled_percentage=0.2  # 20% of users
)

flag_service.create_flag(flag)
print("✅ Feature flag created with 20% rollout")

# Check if enabled for specific user
user_id = "user_99999"
if flag_service.is_enabled("new_summarization_model", user_id=user_id):
    print(f"✅ New model enabled for {user_id}")
    # Use new model
    model = "new-summarization-v2"
else:
    print(f"❌ New model not enabled for {user_id}")
    # Use old model
    model = "old-summarization-v1"

# Gradually increase rollout
flag_service.update_flag("new_summarization_model", percentage=0.5)
print("✅ Rollout increased to 50%")

# Full rollout
flag_service.update_flag(
    "new_summarization_model",
    status=FeatureFlagStatus.ENABLED
)
print("✅ Feature fully enabled for all users")
```

---

## 📡 Using API Endpoints

### Get Gateway Statistics

```bash
curl -X GET http://localhost:5000/api/gateway/stats \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "routes_registered": 15,
    "upstream_services": 4,
    "cache_stats": {
      "hit_rate": 0.78,
      "entry_count": 1456,
      "cache_size_mb": 52.3
    },
    "policy_violations": 8,
    "protocols_supported": ["rest", "graphql", "grpc"]
  }
}
```

### Get Active Chaos Experiments

```bash
curl -X GET http://localhost:5000/api/gateway/chaos/experiments \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Get Circuit Breaker States

```bash
curl -X GET http://localhost:5000/api/gateway/circuit-breakers \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Get Feature Flags

```bash
curl -X GET http://localhost:5000/api/gateway/feature-flags \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

---

## 🎯 Common Use Cases

### Use Case 1: Cost Optimization

```python
from app.services.api_gateway_service import get_gateway_service, RoutingStrategy

gateway = get_gateway_service()

# Always route to cheapest provider
decision = gateway.intelligent_router.route_request(
    model_type="gpt-3.5-turbo",
    estimated_tokens=100,
    strategy=RoutingStrategy.COST_OPTIMIZED
)

print(f"Cheapest option: {decision.service_id}")
print(f"Cost: ${decision.estimated_cost:.4f}")
```

### Use Case 2: Low-Latency Requirements

```python
# For real-time applications, prioritize speed
decision = gateway.intelligent_router.route_request(
    model_type="claude-instant",
    estimated_tokens=50,
    strategy=RoutingStrategy.LATENCY_BASED,
    constraints={'max_latency': 500}  # Must respond in <500ms
)
```

### Use Case 3: Gradual Feature Rollout

```python
# Roll out new feature to 10% -> 25% -> 50% -> 100%
flag_service = get_feature_flag_service()

# Week 1: 10%
flag_service.update_flag("new_feature", percentage=0.1)

# Week 2: 25%
flag_service.update_flag("new_feature", percentage=0.25)

# Week 3: 50%
flag_service.update_flag("new_feature", percentage=0.5)

# Week 4: 100%
flag_service.update_flag("new_feature", status=FeatureFlagStatus.ENABLED)
```

### Use Case 4: Testing Resilience

```python
# Test how system handles increased latency
chaos = get_chaos_service()

experiment = ChaosExperiment(
    experiment_id="load_test",
    name="Peak Load Simulation",
    description="Simulate high-load conditions",
    fault_type=FaultType.LATENCY,
    target_service="all",
    fault_rate=0.5,
    duration_seconds=600
)

chaos.start_experiment(experiment)
# Monitor system behavior for 10 minutes
```

---

## 🔧 Configuration

### Environment Variables

```bash
# Cache configuration
GATEWAY_CACHE_SIZE_MB=100

# Circuit breaker
GATEWAY_CB_FAILURE_THRESHOLD=5
GATEWAY_CB_TIMEOUT_SECONDS=60

# Routing
GATEWAY_DEFAULT_STRATEGY=intelligent
```

### Programmatic Configuration

```python
from app.services.api_gateway_service import APIGatewayService

# Custom configuration
gateway = APIGatewayService()

# Register custom route
from app.services.api_gateway_service import GatewayRoute, ProtocolType

route = GatewayRoute(
    route_id="custom_ai_route",
    path_pattern="/api/v2/ai/*",
    methods=["POST"],
    upstream_service="custom_ai_service",
    protocol=ProtocolType.REST,
    auth_required=True,
    rate_limit=100,
    cache_ttl=300
)

gateway.register_route(route)
```

---

## 📊 Monitoring and Observability

### Get Real-Time Metrics

```python
# Gateway statistics
stats = gateway.get_gateway_stats()
print(f"Cache hit rate: {stats['cache_stats']['hit_rate']:.1%}")
print(f"Active routes: {stats['routes_registered']}")

# Provider statistics
for provider, adapter in gateway.intelligent_router.provider_adapters.items():
    stats = gateway.intelligent_router.provider_stats[provider]
    print(f"{provider}: {stats.total_requests} requests, "
          f"{stats.avg_latency_ms:.0f}ms avg latency")
```

### Monitor Circuit Breakers

```python
cb = get_circuit_breaker()
states = cb.get_all_states()

for service_id, state_info in states.items():
    print(f"{service_id}: {state_info['state']}")
    if state_info['failure_count'] > 0:
        print(f"  Failures: {state_info['failure_count']}")
```

---

## 🎓 Best Practices

1. **Caching Strategy**
   - Cache expensive operations (>1s)
   - Use appropriate TTL (5-15 minutes)
   - Monitor hit rate and adjust

2. **Routing Strategy**
   - COST_OPTIMIZED for batch jobs
   - LATENCY_BASED for real-time
   - INTELLIGENT for general use

3. **Chaos Testing**
   - Start with low fault rates (10-20%)
   - Test during off-peak hours
   - Have rollback plan ready

4. **A/B Testing**
   - Ensure minimum sample size (>1000)
   - Run for adequate duration
   - Track multiple metrics

5. **Canary Deployments**
   - Start with 10% traffic
   - Increment gradually
   - Monitor success rates closely
   - Have automatic rollback enabled

---

## 🆘 Troubleshooting

### Cache not working?

```python
# Check cache stats
stats = gateway.cache.get_stats()
print(f"Hit rate: {stats['hit_rate']}")
print(f"Entries: {stats['entry_count']}")

# If hit rate is 0, check:
# 1. TTL settings
# 2. Cache key generation
# 3. Request variation
```

### Circuit breaker stuck open?

```python
# Manually reset
cb = get_circuit_breaker()
cb.reset("service_name")
print("Circuit breaker reset to CLOSED")
```

### Feature flag not working?

```python
# Check flag status
flags = flag_service.get_all_flags()
print(flags["your_flag_id"])

# Verify user is in rollout percentage
# Hash is deterministic, so same user always gets same result
```

---

## 🚀 Next Steps

- Explore advanced routing strategies
- Set up monitoring dashboards
- Configure custom policies
- Create integration tests
- Set up production deployment

---

**Ready to build superhuman AI applications! 🌟**
