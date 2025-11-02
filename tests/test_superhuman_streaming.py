"""
Test Superhuman Streaming Features
===================================
Tests for breakthrough_streaming.py and ensemble_ai.py

Run with: pytest tests/test_superhuman_streaming.py -v
"""

import asyncio

import pytest

# Mark all tests as not requiring Flask app
pytestmark = pytest.mark.unit


class TestHybridStreamEngine:
    """Test the Hybrid Stream Engine"""

    def test_stream_chunk_creation(self):
        """Test StreamChunk data structure"""
        from app.services.breakthrough_streaming import StreamChunk

        chunk = StreamChunk(
            content="Hello world", confidence=0.95, is_predicted=False, tokens_count=2
        )

        assert chunk.content == "Hello world"
        assert chunk.confidence == 0.95
        assert chunk.is_predicted is False
        assert chunk.tokens_count == 2
        assert chunk.timestamp is not None

    def test_quality_monitor(self):
        """Test QualityMonitor metrics tracking"""
        from app.services.breakthrough_streaming import QualityMonitor

        monitor = QualityMonitor()

        # Record some latencies
        monitor.record_latency(50.0)
        monitor.record_latency(100.0)
        monitor.record_latency(150.0)

        avg_latency = monitor.get_avg_latency()
        assert avg_latency == 100.0

        # Record prediction accuracy
        monitor.record_prediction_accuracy(True)
        monitor.record_prediction_accuracy(True)
        monitor.record_prediction_accuracy(False)

        accuracy = monitor.get_accuracy()
        assert accuracy == pytest.approx(0.666, abs=0.01)

        # Check health score
        health = monitor.get_health_score()
        assert 0.0 <= health <= 1.0

    @pytest.mark.asyncio
    async def test_adaptive_cache(self):
        """Test AdaptiveCache functionality"""
        from app.services.breakthrough_streaming import AdaptiveCache

        cache = AdaptiveCache(max_size=10)

        # Test get_or_compute with sync function
        def compute_value():
            return "computed_value"

        result1 = await cache.get_or_compute("key1", compute_value)
        assert result1 == "computed_value"

        # Should return cached value
        result2 = await cache.get_or_compute("key1", lambda: "new_value")
        assert result2 == "computed_value"  # Cached

        # Test with async function
        async def async_compute():
            await asyncio.sleep(0.01)
            return "async_value"

        result3 = await cache.get_or_compute("key2", async_compute)
        assert result3 == "async_value"

    @pytest.mark.asyncio
    async def test_next_token_predictor(self):
        """Test NextTokenPredictor"""
        from app.services.breakthrough_streaming import NextTokenPredictor

        predictor = NextTokenPredictor()

        # Test prediction
        predictions = await predictor.predict_next({"current_text": "Hello "}, n_tokens=5)

        assert len(predictions) == 5
        for pred in predictions:
            assert "token" in pred
            assert "confidence" in pred
            assert 0.0 <= pred["confidence"] <= 1.0

    def test_hybrid_stream_engine_initialization(self):
        """Test HybridStreamEngine can be initialized"""
        from app.services.breakthrough_streaming import HybridStreamEngine

        engine = HybridStreamEngine()

        assert engine is not None
        assert hasattr(engine, "predictor")
        assert hasattr(engine, "cache")
        assert hasattr(engine, "quality_monitor")

    def test_hybrid_stream_engine_metrics(self):
        """Test metrics retrieval"""
        from app.services.breakthrough_streaming import HybridStreamEngine

        engine = HybridStreamEngine()
        metrics = engine.get_metrics()

        assert "avg_latency_ms" in metrics
        assert "accuracy" in metrics
        assert "health_score" in metrics
        assert "cache_size" in metrics

    @pytest.mark.asyncio
    async def test_hybrid_stream_engine_ultra_stream(self):
        """Test ultra_stream method with mock LLM"""
        from app.services.breakthrough_streaming import HybridStreamEngine

        engine = HybridStreamEngine()

        # Create mock LLM stream
        async def mock_llm_stream():
            tokens = ["Hello", " ", "world", "!"]
            for token in tokens:
                await asyncio.sleep(0.01)
                yield token

        # Test streaming
        chunks = []
        async for chunk in engine.ultra_stream(mock_llm_stream(), {"current_text": ""}):
            chunks.append(chunk)

        assert len(chunks) > 0
        assert all(hasattr(chunk, "content") for chunk in chunks)
        assert all(hasattr(chunk, "confidence") for chunk in chunks)

    def test_get_optimal_chunk_size(self):
        """Test adaptive chunk sizing"""
        from app.services.breakthrough_streaming import HybridStreamEngine

        engine = HybridStreamEngine()

        # Test with different latencies
        # Reset the engine for each test
        engine.quality_monitor.latencies = []

        engine.quality_monitor.record_latency(30.0)  # Fast
        size1 = engine.get_optimal_chunk_size()
        assert size1 == 1  # Token by token

        # Reset and test medium
        engine.quality_monitor.latencies = []
        engine.quality_monitor.record_latency(150.0)  # Medium
        size2 = engine.get_optimal_chunk_size()
        assert size2 == 3

        # Reset and test slow
        engine.quality_monitor.latencies = []
        engine.quality_monitor.record_latency(300.0)  # Slow
        size3 = engine.get_optimal_chunk_size()
        assert size3 == 5

    def test_singleton_pattern(self):
        """Test singleton instance"""
        from app.services.breakthrough_streaming import get_hybrid_engine

        engine1 = get_hybrid_engine()
        engine2 = get_hybrid_engine()

        assert engine1 is engine2  # Same instance


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
        model2, tier2 = await router.route(complex_query, {})
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
