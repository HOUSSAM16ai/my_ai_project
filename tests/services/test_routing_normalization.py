from app.services.api_gateway_service import (
    IntelligentRouter,
    ModelProviderAdapter,
    RoutingStrategy,
)


class MockAdapter(ModelProviderAdapter):
    def __init__(self, cost, latency):
        self.cost = cost
        self.latency = latency

    def call_model(self, model: str, prompt: str, params: dict):
        return {}

    def estimate_cost(self, model: str, tokens: int) -> float:
        return self.cost

    def estimate_latency(self, model: str, tokens: int) -> float:
        return self.latency


def test_routing_scale_normalization():
    """
    Test that the IntelligentRouter correctly normalizes scores so that one factor (e.g. cost)
    doesn't dominate another (e.g. latency) due to raw value magnitude differences.
    """
    router = IntelligentRouter()

    # Provider A: Expensive but Fast
    # Cost: $0.05, Latency: 100ms
    # Weights: Cost 0.3, Latency 0.5.
    # Since Latency weight is higher, a significantly better latency should outweigh the cost penalty
    # if the relative differences are comparable.
    adapter_a = MockAdapter(cost=0.05, latency=100.0)

    # Provider B: Cheap but Slow
    # Cost: $0.001, Latency: 2000ms
    adapter_b = MockAdapter(cost=0.001, latency=2000.0)

    router.provider_adapters = {"provider_a": adapter_a, "provider_b": adapter_b}

    # Reset stats to healthy
    for p in ["provider_a", "provider_b"]:
        router.provider_stats[p].is_healthy = True

    decision = router.route_request(
        model_type="test-model", estimated_tokens=1000, strategy=RoutingStrategy.INTELLIGENT
    )

    # Provider A should be selected because it excels in Latency (which has 0.5 weight)
    # while Provider B is terrible at Latency.
    # Provider B excels in Cost (0.3 weight), but that shouldn't override the massive latency difference
    # when properly normalized.
    assert decision.service_id == "provider_a"
