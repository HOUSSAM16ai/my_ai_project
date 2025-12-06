
import time
from unittest.mock import MagicMock

import pytest
from fastapi import Request

from app.services.api_gateway_service import (
    APIGatewayService,
    IntelligentCache,
    IntelligentRouter,
    PolicyEngine,
    PolicyRule,
    ProtocolType,
    RoutingStrategy,
)


class TestIntelligentRouterComprehensive:
    @pytest.fixture
    def router(self):
        return IntelligentRouter()

    def test_route_request_intelligent_strategy_selection(self, router):
        """Test that intelligent strategy correctly normalizes and scores candidates."""
        # Setup mocks for provider adapters
        mock_openai = MagicMock()
        mock_openai.estimate_cost.return_value = 0.02  # Higher cost
        mock_openai.estimate_latency.return_value = 200.0  # Lower latency

        mock_anthropic = MagicMock()
        mock_anthropic.estimate_cost.return_value = 0.01  # Lower cost
        mock_anthropic.estimate_latency.return_value = 400.0  # Higher latency

        router.provider_adapters = {
            "openai": mock_openai,
            "anthropic": mock_anthropic,
        }

        # Mock stats to be healthy
        router.provider_stats["openai"].is_healthy = True
        router.provider_stats["anthropic"].is_healthy = True

        decision = router.route_request(
            model_type="test-model",
            estimated_tokens=1000,
            strategy=RoutingStrategy.INTELLIGENT
        )

        assert decision is not None
        # With current weights (cost 0.3, latency 0.5, health 0.2), let's see.
        # OpenAI: Cost worst (0.0), Latency best (1.0). Score = 0*0.3 + 1*0.5 + 1*0.2 = 0.7
        # Anthropic: Cost best (1.0), Latency worst (0.0). Score = 1*0.3 + 0*0.5 + 1*0.2 = 0.5
        # So OpenAI should be selected because latency weight is higher.
        assert decision.service_id == "openai"

    def test_route_request_constraints(self, router):
        """Test that constraints exclude providers."""
        mock_openai = MagicMock()
        mock_openai.estimate_cost.return_value = 1.0  # Expensive
        mock_openai.estimate_latency.return_value = 100.0

        router.provider_adapters = {"openai": mock_openai}

        # Constraint max_cost = 0.5
        with pytest.raises(ValueError, match="No suitable provider found"):
            router.route_request(
                model_type="test",
                estimated_tokens=100,
                strategy=RoutingStrategy.COST_OPTIMIZED,
                constraints={"max_cost": 0.5}
            )

    def test_update_provider_stats(self, router):
        """Test statistics updates."""
        provider = "openai"

        # Initial state
        assert router.provider_stats[provider].total_requests == 0

        # Update 1: Success, 100ms
        router.update_provider_stats(provider, success=True, latency_ms=100.0)
        stats = router.provider_stats[provider]
        assert stats.total_requests == 1
        assert stats.avg_latency_ms == 100.0
        assert stats.total_errors == 0
        assert stats.is_healthy is True

        # Update 2: Failure, 200ms
        router.update_provider_stats(provider, success=False, latency_ms=200.0)
        stats = router.provider_stats[provider]
        assert stats.total_requests == 2
        assert stats.total_errors == 1
        # Avg latency: (100 + 200) / 2 = 150
        assert stats.avg_latency_ms == 150.0

        # Error rate is 0.5 (50%), should be unhealthy (threshold is < 0.1)
        assert stats.is_healthy is False


class TestIntelligentCacheComprehensive:
    @pytest.fixture
    def cache(self):
        # Small size for testing eviction
        # 1MB max size
        return IntelligentCache(max_size_mb=1)

    def test_eviction_lru(self, cache):
        """Test Least Recently Used eviction."""
        # Create items. We need to be careful with size calculation.
        # 'data' size is len(json.dumps(data))

        # Item 1: ~300KB
        item1 = {"id": 1, "payload": "x" * 300000}
        cache.put({"req": 1}, item1)

        # Item 2: ~300KB
        item2 = {"id": 2, "payload": "x" * 300000}
        cache.put({"req": 2}, item2)

        # Item 3: ~300KB
        item3 = {"id": 3, "payload": "x" * 300000}
        cache.put({"req": 3}, item3)

        # Total ~900KB. Max is 1MB (1048576 bytes).

        # Access Item 1 and Item 3, making Item 2 the LRU.
        cache.get({"req": 1})
        cache.get({"req": 3})

        # Add Item 4: ~300KB. This should push total over 1MB.
        # Should evict Item 2 (LRU).
        item4 = {"id": 4, "payload": "x" * 300000}
        cache.put({"req": 4}, item4)

        assert cache.get({"req": 1}) is not None
        assert cache.get({"req": 3}) is not None
        assert cache.get({"req": 4}) is not None
        assert cache.get({"req": 2}) is None  # Evicted

    def test_expiration(self, cache):
        """Test TTL expiration."""
        cache.put({"req": "expire"}, {"data": "test"}, ttl_seconds=1)

        # Verify it's there
        assert cache.get({"req": "expire"}) is not None

        # Wait 1.1 seconds
        time.sleep(1.1)

        # Verify it's gone
        assert cache.get({"req": "expire"}) is None
        assert cache.miss_count == 1

    def test_key_generation_fallback(self, cache):
        """Test key generation with non-serializable data."""
        class NonSerializable:
            pass

        bad_obj = NonSerializable()
        req_data = {"obj": bad_obj}

        # Should not raise
        cache.put(req_data, {"ok": True})
        res = cache.get(req_data)
        assert res == {"ok": True}

    def test_large_item_skipping(self, cache):
        """Test that items larger than cache are not stored."""
        # 1.5MB item
        large_item = {"payload": "x" * int(1.5 * 1024 * 1024)}
        cache.put({"req": "large"}, large_item)

        assert cache.get({"req": "large"}) is None
        assert cache.current_size_bytes == 0


class TestPolicyEngineComprehensive:
    @pytest.fixture
    def engine(self):
        return PolicyEngine()

    def test_condition_evaluation_auth(self, engine):
        """Test 'not authenticated' condition."""
        policy = PolicyRule(
            rule_id="auth_check",
            name="Auth Check",
            condition="not authenticated",
            action="deny"
        )
        engine.add_policy(policy)

        # Context is authenticated
        context_auth = {"authenticated": True}
        allowed, reason = engine.evaluate(context_auth)
        assert allowed is True

        # Context is NOT authenticated
        context_no_auth = {"authenticated": False}
        allowed, reason = engine.evaluate(context_no_auth)
        assert allowed is False
        assert "Policy violation" in reason

    def test_condition_evaluation_user_id(self, engine):
        """Test 'user_id required' condition."""
        policy = PolicyRule(
            rule_id="user_check",
            name="User Check",
            condition="user_id required",
            action="deny"
        )
        engine.add_policy(policy)

        # Missing user_id
        allowed, _ = engine.evaluate({"user_id": None})
        assert allowed is False

        # Present user_id
        allowed, _ = engine.evaluate({"user_id": "123"})
        assert allowed is True


class TestAPIGatewayServiceComprehensive:
    @pytest.fixture
    def gateway(self):
        return APIGatewayService()

    @pytest.mark.asyncio
    async def test_process_request_flow_rest(self, gateway):
        """Test standard REST request flow."""
        # Mock Request
        mock_request = MagicMock(spec=Request)
        mock_request.method = "GET"
        mock_request.url.path = "/api/test"
        mock_request.headers = {}
        mock_request.query_params = {}
        # mock_request.json is async
        async def mock_json():
            return {"key": "value"}
        mock_request.json = mock_json
        # Mock state for auth
        mock_request.state.user_id = "user123"

        # Make sure default policy (require_auth) passes
        # It requires auth_required=True (default in Route?) No, the default policy condition is:
        # "auth_required and not authenticated".
        # But wait, 'auth_required' is not in request_context in the code.
        # Let's check APIGatewayService.process_request implementation.
        # request_context = { "user_id": ..., "endpoint": ..., "method": ..., "authenticated": ... }
        # It does NOT seem to inject 'auth_required' into context from the route config yet (code says "Route Request (placeholder)").
        # However, the default policy added in __init__ is: condition="auth_required and not authenticated".
        # If "auth_required" is missing from context, standard python eval/logic might fail or return False?
        # The PolicyEngine._evaluate_condition implementation is:
        # if "not authenticated" in condition: return not context.get("authenticated", False)
        # It does simplified string matching, not eval.

        # So "auth_required and not authenticated" contains "not authenticated".
        # So it returns `not authenticated`.
        # Since we set user_id="user123", authenticated=True. So `not authenticated` is False.
        # So allowed=True.

        response, status = await gateway.process_request(mock_request, ProtocolType.REST)

        assert status == 200
        assert response["status"] == "success"
        # Verify caching occurred (GET request)
        assert gateway.cache.current_size_bytes > 0

        # Second request should be cache hit
        response2, _ = await gateway.process_request(mock_request, ProtocolType.REST)
        assert response2["cache_hit"] is True

    @pytest.mark.asyncio
    async def test_process_request_auth_denied(self, gateway):
        """Test authentication denial."""
        mock_request = MagicMock(spec=Request)
        mock_request.state.user_id = None # Not authenticated

        # The default policy checks "not authenticated" string in condition.
        # See PolicyEngine._evaluate_condition

        response, status = await gateway.process_request(mock_request, ProtocolType.REST)

        assert status == 403
        assert response["status"] == "forbidden"

    @pytest.mark.asyncio
    async def test_process_request_unsupported_protocol(self, gateway):
        """Test invalid protocol."""
        mock_request = MagicMock(spec=Request)

        # Pass a fake protocol enum or just a string if type checking allows,
        # but the method signature expects ProtocolType.
        # Let's use a protocol that is valid Enum but removed from adapters map?
        # Or just simulate a key error if we could.
        # The code does: adapter = self.protocol_adapters.get(protocol.value)
        # If we use ProtocolType.WEBSOCKET, it is not in the default init of APIGatewayService
        # (only REST, GRAPHQL, GRPC are added).

        response, status = await gateway.process_request(mock_request, ProtocolType.WEBSOCKET)

        assert status == 400
        assert "Unsupported protocol" in response["error"]
