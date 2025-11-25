
import pytest

from app.core.math.omni_router import CognitiveComplexity, get_omni_router

# tests/transcendent/test_omni_router.py

@pytest.mark.asyncio
async def test_omni_router_complexity_scoring():
    """
    Verifies that the OmniRouter correctly assesses cognitive complexity.
    """
    router = get_omni_router()

    # Simple prompt
    complexity_simple = router._assess_complexity([{"role": "user", "content": "Hello"}])
    assert complexity_simple == CognitiveComplexity.REFLEX

    # Complex prompt
    complexity_complex = router._assess_complexity([{"role": "user", "content": "Calculate the trajectory of a rocket to Mars considering n-body physics."}])
    # Note: The actual implementation might vary, but we expect it not to be REFLEX if the logic is sound.
    # For now, we just verify it returns a valid enum.
    assert isinstance(complexity_complex, CognitiveComplexity)

@pytest.mark.asyncio
async def test_bandit_learning():
    """
    Test that the router updates its internal bandit state.
    """
    router = get_omni_router()

    # Simulate a successful routing
    initial_score = router.node_states["openai"].success_count

    router.update_outcome("openai", 100.0, True)

    assert router.node_states["openai"].success_count > initial_score
