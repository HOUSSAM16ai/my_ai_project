"""
Test Superhuman Streaming Features
===================================
Tests for breakthrough_streaming.py and ensemble_ai.py

Run with: pytest tests/test_superhuman_streaming.py -v
"""

import pytest

# Mark all tests as not requiring Flask app
pytestmark = pytest.mark.unit


class TestEnsembleAI:
    """Test the Multi-Model Ensemble System"""

    def test_model_tier_enum(self):
        """Test ModelTier enumeration"""
        from app.services.ensemble_ai import ModelTier

        assert ModelTier.NANO.value == "nano"
        assert ModelTier.FAST.value == "fast"
        assert ModelTier.SMART.value == "smart"
        assert ModelTier.GENIUS.value == "genius"

    def test_query_classifier_initialization(self):
        """Test QueryClassifier can be initialized"""
        from app.services.ensemble_ai import QueryClassifier

        classifier = QueryClassifier()
        assert classifier is not None

    @pytest.mark.asyncio
    async def test_query_complexity_calculation(self):
        """Test complexity calculation"""
        from app.services.ensemble_ai import QueryClassifier

        classifier = QueryClassifier()

        # Simple query
        simple_complexity = await classifier.calculate_complexity("Hello")
        assert 0.0 <= simple_complexity <= 1.0

        # Complex query
        complex_query = "Explain the algorithm for implementing a database optimization framework"
        complex_complexity = await classifier.calculate_complexity(complex_query)
        assert complex_complexity > simple_complexity

    def test_query_urgency_detection(self):
        """Test urgency detection"""
        from app.services.ensemble_ai import QueryClassifier

        classifier = QueryClassifier()

        assert classifier.is_urgent("quick answer please") is True
        assert classifier.is_urgent("سريع") is True
        assert classifier.is_urgent("tell me about AI") is False

    def test_query_reasoning_detection(self):
        """Test reasoning detection"""
        from app.services.ensemble_ai import QueryClassifier

        classifier = QueryClassifier()

        assert classifier.needs_reasoning("Why does this work?") is True
        assert classifier.needs_reasoning("Explain the concept") is True
        assert classifier.needs_reasoning("Hello world") is False

    def test_query_domain_detection(self):
        """Test domain detection"""
        from app.services.ensemble_ai import QueryClassifier

        classifier = QueryClassifier()

        assert classifier.detect_domain("Write a function in Python") == "code"
        assert classifier.detect_domain("Design a user interface") == "design"
        assert classifier.detect_domain("Query the database") == "data"
        assert classifier.detect_domain("Hello") == "general"

    def test_cost_optimizer_initialization(self):
        """Test CostOptimizer initialization"""
        from app.services.ensemble_ai import CostOptimizer

        optimizer = CostOptimizer()
        assert optimizer is not None
        assert optimizer.daily_budget > 0

    def test_cost_optimizer_affordability(self):
        """Test cost affordability check"""
        from app.services.ensemble_ai import CostOptimizer, ModelTier

        optimizer = CostOptimizer()

        # Small request should be affordable
        assert optimizer.can_afford(ModelTier.NANO, 1000) is True

        # Very large request might not be affordable
        result = optimizer.can_afford(ModelTier.GENIUS, 10000000)
        assert isinstance(result, bool)

    def test_cost_optimizer_cheaper_alternative(self):
        """Test cheaper alternative suggestion"""
        from app.services.ensemble_ai import CostOptimizer, ModelTier

        optimizer = CostOptimizer()

        # Downgrade from GENIUS
        cheaper = optimizer.suggest_cheaper_alternative(ModelTier.GENIUS)
        assert cheaper == ModelTier.SMART

        # Downgrade from NANO (can't go lower)
        cheapest = optimizer.suggest_cheaper_alternative(ModelTier.NANO)
        assert cheapest == ModelTier.NANO

    def test_intelligent_router_initialization(self):
        """Test IntelligentRouter initialization"""
        from app.services.ensemble_ai import IntelligentRouter

        router = IntelligentRouter()
        assert router is not None
        assert hasattr(router, "classifier")
        assert hasattr(router, "cost_optimizer")

    @pytest.mark.asyncio
    async def test_intelligent_router_route(self):
        """Test routing decision"""
        from app.services.ensemble_ai import IntelligentRouter

        router = IntelligentRouter()

        # Route a simple query
        model, tier = await router.route("Hello", {})
        assert model is not None
        assert tier is not None

        # Route a complex query
        complex_query = "Explain the advanced algorithm for neural network optimization"
        model2, _tier2 = await router.route(complex_query, {})
        assert model2 is not None

    def test_intelligent_router_tier_selection(self):
        """Test tier selection logic"""
        from app.services.ensemble_ai import IntelligentRouter, ModelTier

        router = IntelligentRouter()

        # Simple urgent query -> NANO
        analysis1 = {
            "complexity_score": 0.2,
            "requires_fast_response": True,
            "creativity_score": 0.1,
            "requires_reasoning": False,
        }
        tier1 = router.select_optimal_tier(analysis1)
        assert tier1 == ModelTier.NANO

        # Complex reasoning query -> GENIUS
        analysis2 = {
            "complexity_score": 0.9,
            "requires_fast_response": False,
            "creativity_score": 0.8,
            "requires_reasoning": True,
        }
        tier2 = router.select_optimal_tier(analysis2)
        assert tier2 == ModelTier.GENIUS

    def test_router_singleton(self):
        """Test router singleton"""
        from app.services.ensemble_ai import get_router

        router1 = get_router()
        router2 = get_router()

        assert router1 is router2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
