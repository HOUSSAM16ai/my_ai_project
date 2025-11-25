"""
Unit tests for the Cognitive Fingerprinting module.
"""

import pytest

from app.core.math.cognitive_fingerprint import (
    CognitiveComplexity,
    assess_cognitive_complexity,
)


@pytest.mark.parametrize(
    "prompt, expected_complexity",
    [
        # REFLEX
        ("What is the capital of France?", CognitiveComplexity.REFLEX),
        ("Hello, how are you?", CognitiveComplexity.REFLEX),
        ("Translate 'book' to Spanish.", CognitiveComplexity.REFLEX),
        # THOUGHT
        (
            "Summarize the main points of the article about climate change.",
            CognitiveComplexity.THOUGHT,
        ),
        (
            "Explain the difference between supervised and unsupervised machine learning.",
            CognitiveComplexity.THOUGHT,
        ),
        (
            "What are the implications of quantum computing on modern cryptography?",
            CognitiveComplexity.THOUGHT,
        ),
        # DEEP_THOUGHT (Code)
        ("def factorial(n):", CognitiveComplexity.DEEP_THOUGHT),
        (
            "Write a Python function to find all prime numbers up to n.",
            CognitiveComplexity.DEEP_THOUGHT,
        ),
        ("```javascript\nconst x = 10;\n```", CognitiveComplexity.DEEP_THOUGHT),
        # CREATIVE
        ("Write a short story about a robot who discovers music.", CognitiveComplexity.CREATIVE),
        ("Imagine you are a dragon. Describe your hoard.", CognitiveComplexity.CREATIVE),
        (
            "Create a dialogue between Plato and a modern-day influencer.",
            CognitiveComplexity.CREATIVE,
        ),
        # LOGICAL_REASONING
        ("Solve the following equation for x: 2x + 5 = 15", CognitiveComplexity.LOGICAL_REASONING),
        ("Calculate the derivative of x^3.", CognitiveComplexity.LOGICAL_REASONING),
        (
            "If a train leaves station A at 60 mph and another leaves station B at 70 mph, when will they meet?",
            CognitiveComplexity.LOGICAL_REASONING,
        ),
    ],
)
def test_assess_cognitive_complexity(prompt, expected_complexity):
    """
    Tests that the complexity assessment correctly categorizes various prompts.
    """
    assert assess_cognitive_complexity(prompt) == expected_complexity
