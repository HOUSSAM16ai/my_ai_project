import pytest

from app.core.math.cognitive_fingerprint import CognitiveComplexity, assess_cognitive_complexity


@pytest.mark.parametrize(
    "prompt, expected_complexity",
    [
        # These verify the fix for Math keywords taking precedence over Code keywords
        ("Write a python function to solve a quadratic equation", CognitiveComplexity.DEEP_THOUGHT),
        ("Write a Python function to calculate the factorial", CognitiveComplexity.DEEP_THOUGHT),
        # This verifies that Creative keywords still take precedence (if we move them up)
        # or at least are correctly identified.
        ("Write a poem about a function", CognitiveComplexity.CREATIVE),
        # Standard Math case to ensure it still works
        ("Solve the following equation for x", CognitiveComplexity.LOGICAL_REASONING),
    ],
)
def test_cognitive_complexity_precedence(prompt, expected_complexity):
    """
    Tests the precedence of complexity checks.
    """
    assert assess_cognitive_complexity(prompt) == expected_complexity
