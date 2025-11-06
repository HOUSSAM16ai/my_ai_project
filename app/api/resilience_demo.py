# app/api/resilience_demo.py
# ======================================================================================
# ==    DISTRIBUTED RESILIENCE INTEGRATION DEMO                                       ==
# ======================================================================================
# PRIME DIRECTIVE:
#   عرض توضيحي لكيفية دمج نظام المرونة مع API الموجود
#   Demonstrates integration of resilience patterns with existing APIs
#
# ======================================================================================

from flask import Blueprint, current_app, jsonify, request

from app.services.distributed_resilience_service import (
    BulkheadConfig,
    CircuitBreakerConfig,
    FallbackChain,
    FallbackLevel,
    HealthCheckConfig,
    HealthCheckType,
    HealthChecker,
    PriorityLevel,
    RetryConfig,
    TokenBucket,
    get_resilience_service,
    resilient,
)

# Create blueprint
resilience_demo_bp = Blueprint("resilience_demo", __name__, url_prefix="/api/resilience")

# Initialize service
service = get_resilience_service()

# Configure components
circuit_breaker_config = CircuitBreakerConfig(failure_threshold=5, timeout_seconds=60)

retry_config = RetryConfig(max_retries=3, retry_budget_percent=10.0, base_delay_ms=100)

bulkhead_config = BulkheadConfig(max_concurrent_calls=100, max_queue_size=200)

# Rate limiter for demo
rate_limiter = TokenBucket(capacity=100, refill_rate=10)


# ======================================================================================
# DEMO 1: PROTECTED API ENDPOINT WITH ALL PATTERNS
# ======================================================================================


@resilience_demo_bp.route("/protected-endpoint", methods=["POST"])
def protected_endpoint():
    """
    Demo endpoint showing all resilience patterns
    
    Patterns applied:
    - Rate Limiting (Token Bucket)
    - Bulkhead (Concurrency limit)
    - Circuit Breaker (Failure protection)
    - Retry (With exponential backoff)
    - Fallback Chain (Multi-level degradation)
    """
    # 1. Rate Limiting
    if not rate_limiter.allow():
        return jsonify({"error": "Rate limit exceeded", "retry_after": 60}), 429

    # Get resilience components
    cb = service.get_or_create_circuit_breaker("demo_api", circuit_breaker_config)
    rm = service.get_or_create_retry_manager("demo_api", retry_config)
    bh = service.get_or_create_bulkhead("demo_api", bulkhead_config)

    # 2. Fallback Chain setup
    fallback_chain = FallbackChain()

    def primary_handler():
        """Primary data source - database"""
        data = request.get_json()
        # Simulate database call
        return {"result": "primary", "data": data, "degraded": False}

    def replica_handler():
        """Replica data source"""
        current_app.logger.warning("Falling back to replica")
        return {"result": "replica", "data": {}, "degraded": True}

    def cache_handler():
        """Cached data"""
        current_app.logger.warning("Falling back to cache")
        return {"result": "cache", "data": {}, "degraded": True}

    def default_handler():
        """Default fallback - always succeeds"""
        return {"result": "default", "data": {}, "degraded": True}

    fallback_chain.register_handler(FallbackLevel.PRIMARY, primary_handler)
    fallback_chain.register_handler(FallbackLevel.REPLICA, replica_handler)
    fallback_chain.register_handler(FallbackLevel.DISTRIBUTED_CACHE, cache_handler)
    fallback_chain.register_handler(FallbackLevel.DEFAULT, default_handler)

    try:
        # 3. Apply all patterns: Bulkhead → Circuit Breaker → Retry → Fallback
        result = bh.execute(
            lambda: cb.call(lambda: rm.execute_with_retry(lambda: fallback_chain.execute()[0])),
            priority=PriorityLevel.NORMAL,
        )

        return jsonify(result), 200

    except Exception as e:
        current_app.logger.error(f"All resilience layers failed: {e}")
        return jsonify({"error": "Service unavailable", "details": str(e)}), 503


# ======================================================================================
# DEMO 2: SIMPLE DECORATOR USAGE
# ======================================================================================


@resilience_demo_bp.route("/simple-protected", methods=["GET"])
@resilient(circuit_breaker_name="simple_api", retry_config=RetryConfig(max_retries=2))
def simple_protected_endpoint():
    """
    Simple endpoint using decorator for protection
    
    The @resilient decorator automatically applies:
    - Circuit Breaker
    - Retry with exponential backoff
    """
    data = {"message": "This endpoint is protected by circuit breaker and retry logic", "status": "success"}

    return jsonify(data), 200


# ======================================================================================
# DEMO 3: HEALTH CHECK ENDPOINT
# ======================================================================================


@resilience_demo_bp.route("/health", methods=["GET"])
def health_check_demo():
    """
    Health check endpoint demonstrating health checker
    """
    health_config = HealthCheckConfig(
        check_type=HealthCheckType.DEEP, timeout_seconds=5, grace_period_failures=3
    )

    checker = HealthChecker(health_config)

    def check_function():
        """Simulate health check"""
        # Check database, cache, etc.
        return {
            "database": "connected",
            "cache": "ready",
            "api": "operational",
        }

    result = checker.check(check_function)

    if result.healthy:
        return (
            jsonify(
                {
                    "status": "healthy",
                    "check_type": result.check_type.value,
                    "latency_ms": result.latency_ms,
                    "details": result.details,
                }
            ),
            200,
        )
    else:
        return (
            jsonify(
                {
                    "status": "unhealthy",
                    "check_type": result.check_type.value,
                    "error": result.error,
                    "latency_ms": result.latency_ms,
                }
            ),
            503,
        )


# ======================================================================================
# DEMO 4: COMPREHENSIVE STATS ENDPOINT
# ======================================================================================


@resilience_demo_bp.route("/stats", methods=["GET"])
def resilience_stats():
    """
    Get comprehensive resilience statistics
    
    Returns metrics for:
    - All circuit breakers
    - All retry managers
    - All bulkheads
    - All adaptive timeouts
    """
    stats = service.get_comprehensive_stats()

    return jsonify(stats), 200


# ======================================================================================
# DEMO 5: COMPONENT-SPECIFIC STATS
# ======================================================================================


@resilience_demo_bp.route("/stats/<component_type>/<component_name>", methods=["GET"])
def component_stats(component_type, component_name):
    """
    Get statistics for specific component
    
    Args:
        component_type: 'circuit_breaker', 'retry_manager', or 'bulkhead'
        component_name: Name of the component
    """
    if component_type == "circuit_breaker":
        if component_name in service.circuit_breakers:
            stats = service.circuit_breakers[component_name].get_stats()
            return jsonify(stats), 200

    elif component_type == "retry_manager":
        if component_name in service.retry_managers:
            stats = service.retry_managers[component_name].retry_budget.get_stats()
            return jsonify(stats), 200

    elif component_type == "bulkhead":
        if component_name in service.bulkheads:
            stats = service.bulkheads[component_name].get_stats()
            return jsonify(stats), 200

    return jsonify({"error": "Component not found"}), 404


# ======================================================================================
# DEMO 6: RESET COMPONENT STATE (for testing)
# ======================================================================================


@resilience_demo_bp.route("/reset/<component_type>/<component_name>", methods=["POST"])
def reset_component(component_type, component_name):
    """
    Reset component state (useful for testing)
    
    This is a demo/testing endpoint - not for production use
    """
    if component_type == "circuit_breaker":
        if component_name in service.circuit_breakers:
            # Recreate circuit breaker
            service.circuit_breakers[component_name] = service.get_or_create_circuit_breaker(
                component_name, circuit_breaker_config
            )
            return jsonify({"message": f"Circuit breaker '{component_name}' reset"}), 200

    elif component_type == "retry_manager":
        if component_name in service.retry_managers:
            # Recreate retry manager
            service.retry_managers[component_name] = service.get_or_create_retry_manager(
                component_name, retry_config
            )
            return jsonify({"message": f"Retry manager '{component_name}' reset"}), 200

    return jsonify({"error": "Component not found"}), 404


# ======================================================================================
# USAGE DOCUMENTATION
# ======================================================================================

"""
USAGE EXAMPLES:

1. Test protected endpoint:
   curl -X POST http://localhost:5000/api/resilience/protected-endpoint \
     -H "Content-Type: application/json" \
     -d '{"test": "data"}'

2. Test simple protected endpoint:
   curl http://localhost:5000/api/resilience/simple-protected

3. Check health:
   curl http://localhost:5000/api/resilience/health

4. Get comprehensive stats:
   curl http://localhost:5000/api/resilience/stats

5. Get specific component stats:
   curl http://localhost:5000/api/resilience/stats/circuit_breaker/demo_api

6. Reset component (testing):
   curl -X POST http://localhost:5000/api/resilience/reset/circuit_breaker/demo_api

RATE LIMITING TEST:
   # Run this script to test rate limiting
   for i in {1..150}; do
     curl http://localhost:5000/api/resilience/simple-protected
     echo ""
   done

EXPECTED BEHAVIORS:

1. Circuit Breaker:
   - After 5 consecutive failures, circuit opens
   - Requests fail fast for 60 seconds
   - Then transitions to half-open
   - After 3 successes, closes again

2. Retry:
   - Retries up to 3 times on 5xx errors
   - Uses exponential backoff: 100ms, 200ms, 400ms
   - Applies ±50% jitter
   - Respects retry budget (max 10% retries)

3. Bulkhead:
   - Max 100 concurrent calls
   - Additional calls rejected immediately
   - Queue size: 200
   - Priority-based execution

4. Rate Limiting:
   - Capacity: 100 requests
   - Refill: 10 requests/second
   - Returns 429 when exceeded

5. Fallback Chain:
   - Primary → Replica → Cache → Default
   - Gracefully degrades on failures
   - Sets degraded flag in response
"""
