# tests/test_api_gateway.py
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

class TestIntelligentRouter:
    def test_router_initialization(self):
        router = IntelligentRouter()
        assert router is not None
        assert len(router.provider_adapters) > 0

    def test_cost_optimized_routing(self):
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

class TestIntelligentCache:
    def test_cache_initialization(self):
        cache = IntelligentCache(max_size_mb=10)
        assert cache.max_size_mb == 10
        assert cache.hit_count == 0
        assert cache.miss_count == 0

    def test_cache_put_and_get(self):
        cache = IntelligentCache()
        request_data = {"endpoint": "/api/test", "method": "GET"}
        response_data = {"status": "success", "data": "test"}
        cache.put(request_data, response_data, ttl_seconds=300)
        result = cache.get(request_data)
        assert result is not None
        assert result["status"] == "success"
        assert cache.hit_count == 1

class TestPolicyEngine:
    def test_policy_engine_initialization(self):
        engine = PolicyEngine()
        assert engine is not None
        assert len(engine.policies) == 0

    def test_add_policy(self):
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

class TestProtocolAdapters:
    def test_rest_adapter(self):
        adapter = RESTAdapter()
        is_valid, error = adapter.validate_request(None)
        assert is_valid is True

    def test_graphql_adapter(self):
        adapter = GraphQLAdapter()
        assert adapter is not None

class TestChaosEngineering:
    def test_chaos_service_initialization(self):
        service = ChaosEngineeringService()
        assert service is not None
        assert len(service.active_experiments) == 0

    def test_start_experiment(self):
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

class TestCircuitBreaker:
    def test_circuit_breaker_initialization(self):
        cb = CircuitBreakerService()
        assert cb is not None
        assert cb.config.failure_threshold == 5

    def test_circuit_breaker_success(self):
        cb = CircuitBreakerService()
        def successful_operation():
            return "success"
        success, result, error = cb.call("test_service", successful_operation)
        assert success is True
        assert result == "success"
        assert error is None

class TestABTesting:
    def test_ab_testing_initialization(self):
        service = ABTestingService()
        assert service is not None

    def test_create_experiment(self):
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

class TestCanaryDeployment:
    def test_canary_service_initialization(self):
        service = CanaryDeploymentService()
        assert service is not None

    def test_start_deployment(self):
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

class TestFeatureFlags:
    def test_feature_flag_initialization(self):
        service = FeatureFlagService()
        assert service is not None

    def test_create_flag(self):
        service = FeatureFlagService()
        flag = FeatureFlag(
            flag_id="new_feature",
            name="New Feature",
            description="Test feature",
            status=FeatureFlagStatus.ENABLED,
        )
        result = service.create_flag(flag)
        assert result is True

class TestAPIGatewayService:
    def test_gateway_initialization(self):
        from app.services.api_gateway_service import APIGatewayService
        service = APIGatewayService()
        assert service is not None
