
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from app.core.ai_gateway import NeuralRoutingMesh
from app.core.cognitive_cache import get_cognitive_engine

# --- Mocks ---
class MockCircuitBreaker:
    def allow_request(self): return True
    def record_success(self): pass
    def record_failure(self): pass

@pytest.fixture
def mock_neural_mesh():
    mesh = NeuralRoutingMesh("test_key")
    # Mock nodes to avoid real HTTP calls
    for node in mesh.nodes:
        node.circuit_breaker = MockCircuitBreaker()
        # Mock the internal stream method to avoid ConnectionManager logic
        node_stream_mock = MagicMock()

        async def async_gen(*args, **kwargs):
            yield {"choices": [{"delta": {"content": "Hello"}}]}
            yield {"choices": [{"delta": {"content": " World"}}]}

        mesh._stream_from_node = MagicMock(side_effect=async_gen)
    return mesh

@pytest.mark.asyncio
async def test_cognitive_resonance_cache(mock_neural_mesh):
    """
    Verifies that the Cognitive Resonance Engine correctly:
    1. Misses cache on first unique query.
    2. Caches the response.
    3. Hits cache on a SEMANTICALLY SIMILAR query (not just exact match).
    """
    engine = get_cognitive_engine()
    engine.memory.clear() # Reset state
    engine._stats = {"hits": 0, "misses": 0, "evictions": 0}

    # 1. First Request: "Tell me a joke"
    messages_1 = [{"role": "user", "content": "Tell me a joke about computers"}]

    response_1 = []
    async for chunk in mock_neural_mesh.stream_chat(messages_1):
        response_1.append(chunk)

    assert len(response_1) == 2
    assert engine._stats["misses"] == 1
    assert engine._stats["hits"] == 0

    # Verify it was memorized
    assert len(engine.memory) == 1
    assert engine.memory[0].original_prompt == "Tell me a joke about computers"

    # 2. Second Request: "tell joke computers" (Semantically similar, syntactically different)
    # The normalization should handle case and punctuation. Jaccard/Sequence matcher should handle the rest.
    messages_2 = [{"role": "user", "content": "tell joke computers!!!"}]

    response_2 = []
    async for chunk in mock_neural_mesh.stream_chat(messages_2):
        response_2.append(chunk)

    # Should get exactly the same chunks (cached)
    assert len(response_2) == 2
    assert response_2 == response_1

    # Verify Cache Hit
    assert engine._stats["hits"] == 1
    assert engine._stats["misses"] == 1

@pytest.mark.asyncio
async def test_cognitive_dissonance_no_match(mock_neural_mesh):
    """
    Verifies that distinct queries do NOT trigger a cache hit.
    """
    engine = get_cognitive_engine()
    engine.memory.clear()
    engine._stats = {"hits": 0, "misses": 0, "evictions": 0}

    # 1. "Hello"
    async for _ in mock_neural_mesh.stream_chat([{"role": "user", "content": "Hello"}]): pass

    # 2. "Goodbye"
    async for _ in mock_neural_mesh.stream_chat([{"role": "user", "content": "Goodbye"}]): pass

    # Should be 2 misses
    assert engine._stats["misses"] == 2
    assert len(engine.memory) == 2

    # Reset stats after test to not affect others if order changes
    engine._stats = {"hits": 0, "misses": 0, "evictions": 0}
