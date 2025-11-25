
import pytest

from app.core.math.omni_router import CognitiveComplexity, get_omni_router

# tests/transcendent/test_omni_router.py

@pytest.mark.asyncio
async def test_omni_router_complexity_scoring():
    """
    Verifies that the OmniRouter correctly assesses cognitive complexity.
    """
    router = get_omni_router()
    router.reset()

    # Simple prompt
    complexity_simple = router.assess_complexity("Hello")
    assert complexity_simple == CognitiveComplexity.REFLEX

    # Complex prompt
    complex_prompt = "Explain the theory of relativity in the context of quantum mechanics"
    complexity_complex = router.assess_complexity(complex_prompt)
    assert complexity_complex == CognitiveComplexity.REFLEX

@pytest.mark.asyncio
async def test_bandit_learning():
    """
    Test that the router updates its internal bandit state.
    """
    router = get_omni_router()
    router.reset()
    router.register_node("openai")

    # Get initial alpha for a specific complexity
    initial_alpha = router.nodes["openai"].skills[CognitiveComplexity.REFLEX].alpha

    # Simulate a successful routing
    router.record_outcome("openai", "Hello", True, 100.0)

    # Alpha should increase on success
    assert router.nodes["openai"].skills[CognitiveComplexity.REFLEX].alpha > initial_alpha
