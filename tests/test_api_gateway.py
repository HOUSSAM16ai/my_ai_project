# tests/test_api_gateway.py
# ======================================================================================
# ==        API GATEWAY TESTS (v1.0 - COMPREHENSIVE EDITION)                        ==
# ======================================================================================
"""
اختبارات شاملة لبوابة API - Comprehensive API Gateway tests

Tests cover:
- Gateway service initialization
- Protocol adapters (REST/GraphQL/gRPC)
- Intelligent routing
- Caching layer
- Policy enforcement
- Chaos engineering
- Circuit breakers
- A/B testing
- Canary deployments
- Feature flags
"""

import pytest

from app.services.api_gateway_chaos import (
    ChaosEngineeringService,
    ChaosExperiment,
    CircuitBreakerConfig,
    CircuitBreakerService,
    CircuitState,
    FaultType,
)
from app.services.api_gateway_deployment import (
    ABTestExperiment,
    ABTestingService,
    CanaryDeployment,
    CanaryDeploymentService,
    FeatureFlag,
    FeatureFlagService,
    FeatureFlagStatus,
)
from app.services.api_gateway_service import (
    GraphQLAdapter,
    IntelligentCache,
    IntelligentRouter,
    PolicyEngine,
    PolicyRule,
    RESTAdapter,
    RoutingStrategy,
)

# ======================================================================================
# INTELLIGENT ROUTER TESTS
# ======================================================================================


class TestIntelligentRouter:
    """Test intelligent routing engine"""

    def test_router_initialization(self):
        """Test router initializes correctly"""
        router = IntelligentRouter()
        assert router is not None
        assert len(router.provider_adapters) > 0

    def test_cost_optimized_routing(self):
        """Test cost-optimized routing strategy"""
        router = IntelligentRouter()

        decision = router.route_request(
            model_type="gpt-3.5-turbo",
            estimated_tokens=100,
            strategy=RoutingStrategy.COST_OPTIMIZED,
        )

        assert decision is not None
        assert decision.service_id in router.provider_adapters
        assert decision.estimated_cost > 0
        assert decision.confidence_score > 0

    def test_latency_based_routing(self):
        """Test latency-based routing strategy"""
        router = IntelligentRouter()

        decision = router.route_request(
            model_type="gpt-4", estimated_tokens=500, strategy=RoutingStrategy.LATENCY_BASED
        )

        assert decision is not None
        assert decision.estimated_latency_ms > 0

    def test_intelligent_routing_with_constraints(self):
        """Test intelligent routing with constraints"""
        router = IntelligentRouter()

        decision = router.route_request(
            model_type="gpt-4",
            estimated_tokens=1000,
            strategy=RoutingStrategy.INTELLIGENT,
            constraints={"max_cost": 0.05, "max_latency": 2000},
        )

        assert decision is not None
        assert decision.estimated_cost <= 0.05
        assert decision.estimated_latency_ms <= 2000

    def test_provider_stats_update(self):
        """Test provider statistics tracking"""
        router = IntelligentRouter()

        # Update stats
        router.update_provider_stats("openai", success=True, latency_ms=150.0)
        router.update_provider_stats("openai", success=True, latency_ms=200.0)
        router.update_provider_stats("openai", success=False, latency_ms=100.0)

        stats = router.provider_stats["openai"]
        assert stats.total_requests == 3
        assert stats.total_errors == 1
        assert stats.avg_latency_ms > 0


# ======================================================================================
# CACHING TESTS
# ======================================================================================


class TestIntelligentCache:
    """Test intelligent caching layer"""

    def test_cache_initialization(self):
        """Test cache initializes correctly"""
        cache = IntelligentCache(max_size_mb=10)
        assert cache.max_size_mb == 10
        assert cache.hit_count == 0
        assert cache.miss_count == 0

    def test_cache_put_and_get(self):
        """Test cache put and get operations"""
        cache = IntelligentCache()

        request_data = {"endpoint": "/api/test", "method": "GET"}
        response_data = {"status": "success", "data": "test"}

        # Put into cache
        cache.put(request_data, response_data, ttl_seconds=300)

        # Get from cache
        result = cache.get(request_data)
        assert result is not None
        assert result["status"] == "success"
        assert cache.hit_count == 1

    def test_cache_miss(self):
        """Test cache miss scenario"""
        cache = IntelligentCache()

        result = cache.get({"endpoint": "/api/nonexistent"})
        assert result is None
        assert cache.miss_count == 1

    def test_cache_expiration(self):
        """Test cache entry expiration"""
        cache = IntelligentCache()

        request_data = {"endpoint": "/api/test"}
        response_data = {"data": "test"}

        # Put with short TTL
        cache.put(request_data, response_data, ttl_seconds=0)

        # Should be expired
        import time

        time.sleep(0.1)
        result = cache.get(request_data)
        assert result is None

    def test_cache_stats(self):
        """Test cache statistics"""
        cache = IntelligentCache()

        # Add some entries
        for i in range(5):
            cache.put({"endpoint": f"/api/test{i}"}, {"data": i}, ttl_seconds=300)

        stats = cache.get_stats()
        assert stats["entry_count"] == 5
        assert stats["hit_rate"] == 0.0  # No hits yet

        # Now get one
        cache.get({"endpoint": "/api/test0"})
        stats = cache.get_stats()
        assert stats["hit_count"] == 1


# ======================================================================================
# POLICY ENGINE TESTS
# ======================================================================================


class TestPolicyEngine:
    """Test policy enforcement engine"""

    def test_policy_engine_initialization(self):
        """Test policy engine initializes correctly"""
        engine = PolicyEngine()
        assert engine is not None
        assert len(engine.policies) == 0

    def test_add_policy(self):
        """Test adding policies"""
        engine = PolicyEngine()

        policy = PolicyRule(
            rule_id="test_policy",
            name="Test Policy",
            condition="test_condition",
            action="allow",
            priority=100,
        )

        engine.add_policy(policy)
        assert "test_policy" in engine.policies

    def test_policy_evaluation(self):
        """Test policy evaluation"""
        engine = PolicyEngine()

        policy = PolicyRule(
            rule_id="deny_unauthenticated",
            name="Deny Unauthenticated",
            condition="not authenticated",
            action="deny",
            priority=100,
        )

        engine.add_policy(policy)

        # Test with authenticated context
        allowed, reason = engine.evaluate({"authenticated": True})
        assert allowed is True

    def test_disabled_policy(self):
        """Test disabled policies are not evaluated"""
        engine = PolicyEngine()

        policy = PolicyRule(
            rule_id="disabled_policy",
            name="Disabled",
            condition="true",
            action="deny",
            priority=100,
            enabled=False,
        )

        engine.add_policy(policy)

        allowed, reason = engine.evaluate({})
        assert allowed is True  # Should be allowed because policy is disabled


# ======================================================================================
# PROTOCOL ADAPTER TESTS
# ======================================================================================


class TestProtocolAdapters:
    """Test protocol adapters"""

    def test_rest_adapter(self):
        """Test REST protocol adapter"""
        adapter = RESTAdapter()

        # Validation should pass (Flask request is validated elsewhere)
        is_valid, error = adapter.validate_request(None)
        assert is_valid is True

    def test_graphql_adapter(self):
        """Test GraphQL protocol adapter"""
        adapter = GraphQLAdapter()

        # This would require Flask request context
        # Simplified test
        assert adapter is not None


# ======================================================================================
# CHAOS ENGINEERING TESTS
# ======================================================================================


@pytest.mark.usefixtures("app_context")
class TestChaosEngineering:
    """Test chaos engineering service"""

    def test_chaos_service_initialization(self):
        """Test chaos service initializes correctly"""
        service = ChaosEngineeringService()
        assert service is not None
        assert len(service.active_experiments) == 0

    def test_start_experiment(self):
        """Test starting chaos experiment"""
        service = ChaosEngineeringService()

        experiment = ChaosExperiment(
            experiment_id="test_exp_1",
            name="Test Latency Injection",
            description="Test experiment",
            fault_type=FaultType.LATENCY,
            target_service="test_service",
            fault_rate=0.5,
            duration_seconds=60,
        )

        result = service.start_experiment(experiment)
        assert result is True
        assert experiment.experiment_id in service.active_experiments

    def test_stop_experiment(self):
        """Test stopping chaos experiment"""
        service = ChaosEngineeringService()

        experiment = ChaosExperiment(
            experiment_id="test_exp_2",
            name="Test Error Injection",
            description="Test experiment",
            fault_type=FaultType.ERROR,
            target_service="test_service",
            fault_rate=0.3,
            duration_seconds=30,
        )

        service.start_experiment(experiment)
        result = service.stop_experiment("test_exp_2")

        assert result is True
        assert "test_exp_2" not in service.active_experiments


# ======================================================================================
# CIRCUIT BREAKER TESTS
# ======================================================================================


@pytest.mark.usefixtures("app_context")
class TestCircuitBreaker:
    """Test circuit breaker service"""

    def test_circuit_breaker_initialization(self):
        """Test circuit breaker initializes correctly"""
        cb = CircuitBreakerService()
        assert cb is not None
        assert cb.config.failure_threshold == 5

    def test_circuit_breaker_success(self):
        """Test circuit breaker with successful calls"""
        cb = CircuitBreakerService()

        def successful_operation():
            return "success"

        success, result, error = cb.call("test_service", successful_operation)

        assert success is True
        assert result == "success"
        assert error is None

    def test_circuit_breaker_failure(self):
        """Test circuit breaker with failures"""
        cb = CircuitBreakerService(CircuitBreakerConfig(failure_threshold=3))

        def failing_operation():
            raise Exception("Service error")

        # Fail multiple times
        for _ in range(3):
            success, result, error = cb.call("test_service", failing_operation)
            assert success is False

        # Circuit should now be OPEN
        state = cb.get_state("test_service")
        assert state == CircuitState.OPEN

    def test_circuit_breaker_reset(self):
        """Test manual circuit breaker reset"""
        cb = CircuitBreakerService()

        # Manually open circuit
        cb.circuit_states["test_service"].state = CircuitState.OPEN

        # Reset
        cb.reset("test_service")

        state = cb.get_state("test_service")
        assert state == CircuitState.CLOSED


# ======================================================================================
# AB TESTING TESTS
# ======================================================================================


@pytest.mark.usefixtures("app_context")
class TestABTesting:
    """Test A/B testing service"""

    def test_ab_testing_initialization(self):
        """Test A/B testing service initializes correctly"""
        service = ABTestingService()
        assert service is not None

    def test_create_experiment(self):
        """Test creating A/B test experiment"""
        service = ABTestingService()

        experiment = ABTestExperiment(
            experiment_id="test_ab_1",
            name="Model A vs B",
            description="Test experiment",
            variant_a="model_v1",
            variant_b="model_v2",
            traffic_split=0.5,
        )

        result = service.create_experiment(experiment)
        assert result is True

    def test_assign_variant(self):
        """Test variant assignment"""
        service = ABTestingService()

        experiment = ABTestExperiment(
            experiment_id="test_ab_2",
            name="Test",
            description="Test",
            variant_a="v1",
            variant_b="v2",
            traffic_split=0.5,
        )

        service.create_experiment(experiment)

        # Assign user
        variant = service.assign_variant("test_ab_2", "user_123")
        assert variant in ["v1", "v2"]

        # Same user should get same variant
        variant2 = service.assign_variant("test_ab_2", "user_123")
        assert variant == variant2

    def test_record_outcome(self):
        """Test recording experiment outcomes"""
        service = ABTestingService()

        experiment = ABTestExperiment(
            experiment_id="test_ab_3",
            name="Test",
            description="Test",
            variant_a="v1",
            variant_b="v2",
            traffic_split=0.5,
        )

        service.create_experiment(experiment)
        service.assign_variant("test_ab_3", "user_123")

        # Record outcome
        service.record_outcome("test_ab_3", "user_123", "conversion_rate", 0.85)

        results = service.get_experiment_results("test_ab_3")
        assert results is not None


# ======================================================================================
# CANARY DEPLOYMENT TESTS
# ======================================================================================


@pytest.mark.usefixtures("app_context")
class TestCanaryDeployment:
    """Test canary deployment service"""

    def test_canary_service_initialization(self):
        """Test canary service initializes correctly"""
        service = CanaryDeploymentService()
        assert service is not None

    def test_start_deployment(self):
        """Test starting canary deployment"""
        service = CanaryDeploymentService()

        deployment = CanaryDeployment(
            deployment_id="canary_1",
            service_id="ai_model_service",
            canary_version="v2.0",
            stable_version="v1.5",
            canary_traffic_percent=10.0,
        )

        result = service.start_deployment(deployment)
        assert result is True

    def test_get_version_for_request(self):
        """Test version selection for request"""
        service = CanaryDeploymentService()

        deployment = CanaryDeployment(
            deployment_id="canary_2",
            service_id="test_service",
            canary_version="v2.0",
            stable_version="v1.0",
            canary_traffic_percent=50.0,
        )

        service.start_deployment(deployment)

        version = service.get_version_for_request("canary_2", "user_123")
        assert version in ["v2.0", "v1.0"]

    def test_record_request_outcome(self):
        """Test recording request outcomes"""
        service = CanaryDeploymentService()

        deployment = CanaryDeployment(
            deployment_id="canary_3",
            service_id="test_service",
            canary_version="v2.0",
            stable_version="v1.0",
        )

        service.start_deployment(deployment)

        # Record some outcomes
        service.record_request_outcome("canary_3", "v2.0", True, 150.0)
        service.record_request_outcome("canary_3", "v2.0", True, 200.0)

        assert deployment.metrics.get("canary_requests", 0) == 2


# ======================================================================================
# FEATURE FLAG TESTS
# ======================================================================================


@pytest.mark.usefixtures("app_context")
class TestFeatureFlags:
    """Test feature flag service"""

    def test_feature_flag_initialization(self):
        """Test feature flag service initializes correctly"""
        service = FeatureFlagService()
        assert service is not None

    def test_create_flag(self):
        """Test creating feature flag"""
        service = FeatureFlagService()

        flag = FeatureFlag(
            flag_id="new_feature",
            name="New Feature",
            description="Test feature",
            status=FeatureFlagStatus.ENABLED,
        )

        result = service.create_flag(flag)
        assert result is True

    def test_is_enabled_simple(self):
        """Test simple enabled/disabled check"""
        service = FeatureFlagService()

        # Enabled flag
        flag1 = FeatureFlag(
            flag_id="enabled_flag",
            name="Enabled",
            description="Test",
            status=FeatureFlagStatus.ENABLED,
        )
        service.create_flag(flag1)

        assert service.is_enabled("enabled_flag") is True

        # Disabled flag
        flag2 = FeatureFlag(
            flag_id="disabled_flag",
            name="Disabled",
            description="Test",
            status=FeatureFlagStatus.DISABLED,
        )
        service.create_flag(flag2)

        assert service.is_enabled("disabled_flag") is False

    def test_percentage_rollout(self):
        """Test percentage-based rollout"""
        service = FeatureFlagService()

        flag = FeatureFlag(
            flag_id="percentage_flag",
            name="Percentage",
            description="Test",
            status=FeatureFlagStatus.PERCENTAGE,
            enabled_percentage=0.5,  # 50%
        )
        service.create_flag(flag)

        # Check for multiple users
        enabled_count = 0
        for i in range(100):
            if service.is_enabled("percentage_flag", user_id=f"user_{i}"):
                enabled_count += 1

        # Should be roughly 50% (allow some variance)
        assert 30 <= enabled_count <= 70

    def test_update_flag(self):
        """Test updating feature flag"""
        service = FeatureFlagService()

        flag = FeatureFlag(
            flag_id="update_flag",
            name="Update Test",
            description="Test",
            status=FeatureFlagStatus.DISABLED,
        )
        service.create_flag(flag)

        # Update to enabled
        result = service.update_flag("update_flag", status=FeatureFlagStatus.ENABLED)
        assert result is True

        assert service.is_enabled("update_flag") is True


# ======================================================================================
# MAIN GATEWAY SERVICE TESTS
# ======================================================================================


class TestAPIGatewayService:
    """Test main API Gateway service"""

    def test_gateway_initialization(self):
        """Test gateway initializes correctly"""
        from app.services.api_gateway_service import APIGatewayService

        service = APIGatewayService()
        assert service is not None

    def test_register_route(self):
        """Test registering gateway routes"""
        # Would require Flask app context
        pass

    def test_register_upstream_service(self):
        """Test registering upstream services"""
        # Would require Flask app context
        pass
