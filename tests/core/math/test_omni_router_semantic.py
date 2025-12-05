import pytest

from app.core.math.omni_router import OmniCognitiveRouter, SemanticAffinityEngine


class TestSemanticAffinityEngine:
    def test_coding_affinity(self):
        engine = SemanticAffinityEngine()

        # Test Coder model with Coding prompt
        prompt = "write a python function to fix a bug"
        model = "super-coder-v1"
        score = engine.get_affinity_score(prompt, model)
        assert score > 1.0, "Coder model should get a boost for coding prompt"

        # Test Creative model with Coding prompt
        model_creative = "story-wizard"
        score_creative = engine.get_affinity_score(prompt, model_creative)
        assert score_creative == 1.0, "Creative model should not get a boost for coding prompt"

    def test_creative_affinity(self):
        engine = SemanticAffinityEngine()
        prompt = "Write a creative story about a robot"
        model = "story-wizard"
        score = engine.get_affinity_score(prompt, model)
        assert score > 1.0

    def test_neutral_prompt(self):
        engine = SemanticAffinityEngine()
        prompt = "hello how are you"
        model = "any-model"
        score = engine.get_affinity_score(prompt, model)
        assert score == 1.0


class TestOmniCognitiveRouterSemantic:
    def test_ranking_with_semantics(self):
        router = OmniCognitiveRouter()

        # Setup: Two models
        # Model A: "coder-pro"
        # Model B: "poet-pro"

        # MOCK the sample method to return equal values
        # This isolates the semantic affinity logic
        with pytest.MonkeyPatch.context() as m:
            # We mock OmniNodeState.sample.
            # Note: node instances are created inside get_ranked_nodes if not present.
            # So we better mock the class method.
            from app.core.math.omni_router import OmniNodeState

            m.setattr(OmniNodeState, "sample", lambda self, complexity: 0.5)

            prompt = "write python code"
            models = ["coder-pro", "poet-pro"]

            # "coder-pro" matches "coder" domain -> Semantic Boost
            # "poet-pro" does not -> No boost
            # Base score 0.5 for both.
            # Coder score = 0.5 * 1.25 = 0.625
            # Poet score = 0.5 * 1.0 = 0.5

            ranked = router.get_ranked_nodes(models, prompt)

            # Coder-pro should be first
            assert ranked[0] == "coder-pro"

            # Now try a poem prompt
            prompt_poem = "write a poem"
            # "poet-pro" is not in our keyword map, so let's use a known key "wizard"
            models_v2 = ["coder-pro", "wizard-lm"]

            ranked_poem = router.get_ranked_nodes(models_v2, prompt_poem)
            # wizard-lm matches "creative" (write a poem).
            # coder-pro does not.

            assert ranked_poem[0] == "wizard-lm"
