
import pytest
import time
from app.core.math.omni_router import get_omni_router, CognitiveComplexity

class TestOmniCognitiveRouter:
    """
    Verifies the God-Mode capabilities of the Omni-Cognitive Router.
    """

    def test_complexity_assessment(self):
        """
        Verify the router correctly identifies the cognitive load of a prompt.
        """
        router = get_omni_router()
        router.reset() # Ensure clean state

        # Reflex
        assert router.assess_complexity("Hello world") == CognitiveComplexity.REFLEX

        # Thought
        long_prompt = "A" * 600
        assert router.assess_complexity(long_prompt) == CognitiveComplexity.THOUGHT

        # Deep Thought (Code)
        long_code = "def test(): pass " + (" " * 501)
        assert router.assess_complexity(long_code) == CognitiveComplexity.DEEP_THOUGHT

        # Deep Thought (Length)
        very_long = "A" * 2001
        assert router.assess_complexity(very_long) == CognitiveComplexity.DEEP_THOUGHT

    def test_kalman_filtering_denoising(self):
        """
        Verify that the Kalman filter correctly smooths out latency spikes.
        """
        router = get_omni_router()
        router.reset()
        model_id = "test-model-kalman"

        # Initial state should be around 1000ms
        router.register_node(model_id)
        node = router.nodes[model_id]
        initial_estimate = node.kalman_filter.get_estimate()
        assert initial_estimate == 1000.0

        # Inject a series of stable measurements (e.g., 100ms)
        # The estimate should drift towards 100ms over time
        for _ in range(10):
            node.update(CognitiveComplexity.REFLEX, success=True, raw_latency_ms=100.0)

        current_estimate = node.kalman_filter.get_estimate()
        assert current_estimate < 1000.0
        assert current_estimate > 80.0 # Should have moved significantly towards 100

        # Inject a MASSIVE spike (e.g., 10000ms - GC pause or network blip)
        # The Kalman filter should treat this as noise (high R) and not jump to 10000
        prev_estimate = current_estimate
        node.update(CognitiveComplexity.REFLEX, success=True, raw_latency_ms=10000.0)

        new_estimate = node.kalman_filter.get_estimate()

        change = new_estimate - prev_estimate
        # Ensure it didn't jump insanely high (e.g., didn't go up by 2000ms)
        # With R=5000, Q=1, K ~ 0.0002. Jump should be tiny.
        # Wait, P converges. P_ss = sqrt(Q*R) approx?
        # Q=1, R=5000 -> P will settle low. K will be small.
        assert change < 2000.0

    def test_contextual_bandit_learning(self):
        """
        Verify that the router learns different preferences for different contexts.
        """
        router = get_omni_router()
        router.reset()

        model_a = "model-reflex-specialist"
        model_b = "model-deep-thought-specialist"

        # Prompt generators
        prompt_reflex = "short"
        prompt_deep = "def " * 600 # > 2000 chars, code

        # Train Model A to be good at Reflex, bad at Deep Thought
        # Train Model B to be bad at Reflex, good at Deep Thought

        # Training Phase
        for _ in range(100):
            # Model A: Fast/Good on Reflex
            router.record_outcome(model_a, prompt_reflex, success=True, latency_ms=100)
            # Model A: Slow/Bad on Deep Thought
            router.record_outcome(model_a, prompt_deep, success=False, latency_ms=5000)

            # Model B: Slow/Bad on Reflex
            router.record_outcome(model_b, prompt_reflex, success=False, latency_ms=2000)
            # Model B: Fast/Good on Deep Thought
            router.record_outcome(model_b, prompt_deep, success=True, latency_ms=500)

        # Evaluation Phase

        # 1. Ask for Reflex Task
        ranked_reflex = router.get_ranked_nodes([model_a, model_b], prompt_reflex)
        # Model A should be top
        assert ranked_reflex[0] == model_a

        # 2. Ask for Deep Thought Task
        ranked_deep = router.get_ranked_nodes([model_a, model_b], prompt_deep)
        # Model B should be top
        assert ranked_deep[0] == model_b
