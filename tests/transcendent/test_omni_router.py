import pytest

from app.core.math.cognitive_fingerprint import CognitiveComplexity
from app.core.math.omni_router import get_omni_router


@pytest.mark.asyncio
async def test_bandit_learning_across_complexities():
    """
    Test that the router updates its internal bandit state correctly
    for different cognitive complexities after the upgrade.
    """
    router = get_omni_router()
    router.reset()
    router.register_node("anthropic")
    router.register_node("google")

    # 1. Test REFLEX complexity
    prompt_reflex = "What time is it?"
    initial_alpha_reflex = router.nodes["anthropic"].skills[CognitiveComplexity.REFLEX].alpha
    router.record_outcome("anthropic", prompt_reflex, True, 120.0)
    assert router.nodes["anthropic"].skills[CognitiveComplexity.REFLEX].alpha > initial_alpha_reflex

    # 2. Test CREATIVE complexity
    prompt_creative = "Write a haiku about servers."
    initial_alpha_creative = router.nodes["google"].skills[CognitiveComplexity.CREATIVE].alpha
    router.record_outcome("google", prompt_creative, True, 2500.0)
    assert (
        router.nodes["google"].skills[CognitiveComplexity.CREATIVE].alpha > initial_alpha_creative
    )

    # 3. Test that other complexities are not affected
    assert (
        router.nodes["anthropic"].skills[CognitiveComplexity.CREATIVE].alpha
        == initial_alpha_creative
    )


@pytest.mark.asyncio
async def test_ranking_based_on_performance_deterministic(monkeypatch):
    """
    Tests that the router ranks nodes based on their learned performance
    for a specific complexity, with deterministic sampling.
    """
    # Replace random sampling with a deterministic function for this test
    monkeypatch.setattr(
        "app.core.math.omni_router.random.betavariate", lambda alpha, beta: alpha / (alpha + beta)
    )

    router = get_omni_router()
    router.reset()

    model_fast = "model-fast"
    model_slow = "model-slow"
    available_models = [model_fast, model_slow]

    prompt_code = "Implement a quicksort algorithm in Rust."  # DEEP_THOUGHT

    # Simulate a history where model-fast is consistently better for coding
    for _ in range(10):  # No need for 100 iterations with deterministic test
        router.record_outcome(model_fast, prompt_code, True, 1000.0)  # Fast and successful
        router.record_outcome(model_slow, prompt_code, True, 5000.0)  # Slow and successful

    # Now, ask for a ranking for a similar task
    ranked_nodes = router.get_ranked_nodes(available_models, prompt_code)

    # model-fast should be ranked higher than model-slow
    assert ranked_nodes[0] == model_fast
    assert ranked_nodes[1] == model_slow
