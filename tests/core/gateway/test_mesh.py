from app.core.gateway.circuit_breaker import CircuitBreaker
from app.core.gateway.mesh import NeuralRoutingMesh, SAFETY_NET_MODEL_ID, _DefaultOmniRouter
from app.core.gateway.node import NeuralNode


def test_default_omni_router_orders_safety_net_last():
    router = _DefaultOmniRouter()
    nodes_map = {
        "model-a": NeuralNode(model_id="model-a", circuit_breaker=CircuitBreaker("a")),
        SAFETY_NET_MODEL_ID: NeuralNode(
            model_id=SAFETY_NET_MODEL_ID, circuit_breaker=CircuitBreaker("safety")
        ),
    }
    router.set_nodes_map(nodes_map)

    ranked = router.get_ranked_nodes([])

    assert ranked == ["model-a", SAFETY_NET_MODEL_ID]


def test_neural_routing_mesh_prioritizes_ranked_nodes():
    mesh = NeuralRoutingMesh(api_key="dummy")
    mesh.nodes_map.update(
        {
            "model-b": NeuralNode(model_id="model-b", circuit_breaker=CircuitBreaker("b")),
            "model-a": NeuralNode(model_id="model-a", circuit_breaker=CircuitBreaker("a")),
        }
    )
    if isinstance(mesh.omni_router, _DefaultOmniRouter):
        mesh.omni_router.set_nodes_map(mesh.nodes_map)

    prioritized = mesh._get_prioritized_nodes([{"role": "user", "content": "hi"}])

    assert [node.model_id for node in prioritized][:2] == ["model-b", "model-a"]
