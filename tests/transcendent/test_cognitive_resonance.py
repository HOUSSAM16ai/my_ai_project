import pytest

from app.core.cognitive_cache import CognitiveResonanceEngine


from unittest.mock import patch


@pytest.mark.asyncio
async def test_cognitive_resonance_caching():
    """
    Test that the resonance engine correctly caches and retrieves items based on semantic similarity.
    """
    engine = CognitiveResonanceEngine()
    # Reset stats for test isolation
    engine._stats = {"hits": 0, "misses": 0, "evictions": 0}
    engine.memory.clear()

    # Patch the threshold to make the test less brittle
    with patch("app.core.cognitive_cache.RESONANCE_THRESHOLD", 0.5):
        # 1. Memorize an item
        prompt1 = "Tell me a joke about computers."
        response1 = [{"role": "assistant", "content": "Why did the computer cross the road?"}]
        engine.memorize(prompt1, "context1", response1)
        assert engine.get_stats()["memory_usage"] == 1

        # 2. Recall an item with a semantically similar prompt
        recall_prompt = "Can you tell me a computer joke?"
        retrieved = engine.recall(recall_prompt, "context1")
        assert retrieved is not None
        assert retrieved[0]["content"] == "Why did the computer cross the road?"
        assert engine.get_stats()["hits"] == 1

        # 3. Fail to recall with a different prompt
        retrieved_fail = engine.recall("What is the weather like?", "context1")
        assert retrieved_fail is None
        assert engine.get_stats()["misses"] == 1

        # 4. Fail to recall with a different context
        retrieved_fail_context = engine.recall(prompt1, "context2")
        assert retrieved_fail_context is None
        assert engine.get_stats()["misses"] == 2
