"""
Tests for Ensemble AI Service
=============================
"""

from unittest.mock import MagicMock, patch

import pytest

from app.services.ensemble_ai import (
    CostOptimizer,
    IntelligentRouter,
    ModelTier,
    QueryClassifier,
    get_router,
)

# === QueryClassifier Tests ===


class TestQueryClassifier:
    @pytest.mark.asyncio
    async def test_calculate_complexity_simple(self):
        classifier = QueryClassifier()
        complexity = await classifier.calculate_complexity("hello world")
        assert complexity < 0.3

    @pytest.mark.asyncio
    async def test_calculate_complexity_complex(self):
        classifier = QueryClassifier()
        # Add "step by step" to trigger multi-step factor (0.3 weight)
        # Add more tech terms
        query = "Explain step by step the algorithm for database optimization using a specialized framework architecture and implementation details for deployment"
        complexity = await classifier.calculate_complexity(query)
        assert complexity > 0.4

    def test_count_technical_terms(self):
        classifier = QueryClassifier()
        count = classifier.count_technical_terms("implement algorithm for database api")
        assert count >= 3

    def test_is_multi_step(self):
        classifier = QueryClassifier()
        assert classifier.is_multi_step("First do this, then do that")
        assert not classifier.is_multi_step("Simple question")

    @pytest.mark.asyncio
    async def test_measure_ambiguity(self):
        classifier = QueryClassifier()
        high = await classifier.measure_ambiguity("what is it")
        low = await classifier.measure_ambiguity("explain quantum physics in detail please")
        assert high > low

    def test_assess_creativity_need(self):
        classifier = QueryClassifier()
        score = classifier.assess_creativity_need("create a design for a new logo")
        assert score > 0

    def test_is_urgent(self):
        classifier = QueryClassifier()
        assert classifier.is_urgent("I need help now urgent")
        assert not classifier.is_urgent("take your time")

    def test_detect_domain(self):
        classifier = QueryClassifier()
        assert classifier.detect_domain("debug this code function") == "code"
        assert classifier.detect_domain("sql query database") == "data"
        assert classifier.detect_domain("design ui interface") == "design"
        assert classifier.detect_domain("random stuff") == "general"

    def test_estimate_response_length(self):
        classifier = QueryClassifier()
        assert classifier.estimate_response_length("give a brief summary") == "short"
        assert classifier.estimate_response_length("explain in detail") == "long"
        assert classifier.estimate_response_length("what is python") == "medium"

    def test_needs_reasoning(self):
        classifier = QueryClassifier()
        assert classifier.needs_reasoning("why is the sky blue")
        assert classifier.needs_reasoning("compare x and y")
        assert not classifier.needs_reasoning("print hello")

    @pytest.mark.asyncio
    async def test_analyze_integration(self):
        classifier = QueryClassifier()
        analysis = await classifier.analyze(
            "explain how to optimize database query step by step", {}
        )
        assert "complexity_score" in analysis
        assert "domain" in analysis
        assert analysis["domain"] == "data"
        assert analysis["requires_reasoning"] is True


# === CostOptimizer Tests ===


class TestCostOptimizer:
    def test_can_afford(self):
        optimizer = CostOptimizer()
        optimizer.daily_budget = 100.0
        optimizer.spent_today = 99.999
        # Tier NANO is cheap (0.0001 per 1k)
        assert optimizer.can_afford(ModelTier.NANO, 1000)
        # Tier GENIUS is expensive (0.05 per 1k)
        # 1000 tokens = 0.05 USD. 99.999 + 0.05 > 100.
        assert not optimizer.can_afford(ModelTier.GENIUS, 1000)

    def test_suggest_cheaper_alternative(self):
        optimizer = CostOptimizer()
        assert optimizer.suggest_cheaper_alternative(ModelTier.GENIUS) == ModelTier.SMART
        assert optimizer.suggest_cheaper_alternative(ModelTier.FAST) == ModelTier.NANO
        assert optimizer.suggest_cheaper_alternative(ModelTier.NANO) == ModelTier.NANO

    def test_record_cost(self):
        optimizer = CostOptimizer()
        initial = optimizer.spent_today
        optimizer.record_cost(ModelTier.SMART, 1000)  # 0.01
        assert optimizer.spent_today > initial
        assert optimizer.spent_today == initial + 0.01


# === IntelligentRouter Tests ===


class TestIntelligentRouter:
    @pytest.fixture
    def router(self):
        # Patch get_ai_config to return mock
        with patch("app.config.ai_models.get_ai_config") as mock_get_config:
            mock_config = MagicMock()
            mock_config.tier_nano = "nano-model"
            mock_config.tier_fast = "fast-model"
            mock_config.tier_smart = "smart-model"
            mock_config.tier_genius = "genius-model"
            mock_get_config.return_value = mock_config
            return IntelligentRouter()

    @pytest.mark.asyncio
    async def test_route_simple_urgent(self, router):
        query = "quick help"  # Urgent, simple
        model, tier = await router.route(query, {})
        assert tier == ModelTier.NANO
        assert model == "nano-model"

    @pytest.mark.asyncio
    async def test_route_simple_not_urgent(self, router):
        query = "what is 2+2"  # Simple, not urgent, no reasoning
        model, tier = await router.route(query, {})
        assert tier == ModelTier.FAST
        assert model == "fast-model"

    @pytest.mark.asyncio
    async def test_route_medium(self, router):
        # Trigger SMART: Complexity >= 0.4
        # "algorithm function class implement framework step by step"
        query = "implement a class function algorithm using framework step by step"
        _model, tier = await router.route(query, {})
        assert tier in [ModelTier.SMART, ModelTier.GENIUS]

    @pytest.mark.asyncio
    async def test_route_complex(self, router):
        query = "complex query"
        # Mock analysis to force GENIUS routing
        # Complexity >= 0.7 AND (reasoning OR creativity >= 0.5)
        with patch.object(
            router.classifier,
            "analyze",
            return_value={
                "complexity_score": 0.8,
                "creativity_score": 0.6,
                "requires_fast_response": False,
                "domain": "code",
                "expected_length": "long",
                "requires_reasoning": True,
            },
        ):
            model, tier = await router.route(query, {})
            assert tier == ModelTier.GENIUS
            assert model == "genius-model"

    @pytest.mark.asyncio
    async def test_route_cost_downgrade(self, router):
        router.cost_optimizer.daily_budget = 0.000001  # Almost zero
        router.cost_optimizer.spent_today = 100.0  # Already over budget

        # Should normally be GENIUS
        query = "explain complex thing"
        _model, tier = await router.route(query, {})

        # Should be downgraded
        assert tier != ModelTier.GENIUS
        pass

    def test_get_next_tier(self, router):
        assert router.get_next_tier(ModelTier.NANO) == ModelTier.FAST
        assert router.get_next_tier(ModelTier.GENIUS) == ModelTier.GENIUS


def test_get_router_singleton():
    r1 = get_router()
    r2 = get_router()
    assert r1 is r2
