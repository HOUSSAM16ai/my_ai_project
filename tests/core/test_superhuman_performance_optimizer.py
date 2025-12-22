

import pytest

from app.core.superhuman_performance_optimizer import (
    SuperhumanPerformanceOptimizer,
    get_performance_optimizer,
    reset_optimizer,
)


@pytest.fixture
def optimizer():
    reset_optimizer()
    return get_performance_optimizer()

@pytest.mark.asyncio
async def test_optimizer_initialization(optimizer):
    assert isinstance(optimizer, SuperhumanPerformanceOptimizer)
    assert optimizer.total_requests == 0
    assert optimizer.metrics == {}

@pytest.mark.asyncio
async def test_record_request(optimizer):
    model_id = "test-model-v1"

    optimizer.record_request(
        model_id=model_id,
        success=True,
        latency_ms=100.0,
        tokens=50,
        quality_score=0.9
    )

    metrics = optimizer.metrics[model_id]
    assert metrics.total_requests == 1
    assert metrics.successful_requests == 1
    assert metrics.failed_requests == 0
    assert metrics.avg_latency_ms == 100.0
    assert metrics.total_tokens == 50
    assert metrics.avg_quality_score == 0.9

@pytest.mark.asyncio
async def test_model_selection(optimizer):
    models = ["model-a", "model-b"]

    # Run selection multiple times
    selected = set()
    for _ in range(100):
        selected.add(optimizer.get_recommended_model(models))

    # Should pick from available models
    assert selected.issubset(set(models))

@pytest.mark.asyncio
async def test_adaptive_metrics_update(optimizer):
    model_id = "test-latency"

    # Add varying latencies
    latencies = [10.0, 20.0, 30.0, 40.0, 50.0]
    for lat in latencies:
        optimizer.record_request(model_id, True, lat)

    metrics = optimizer.metrics[model_id]
    assert metrics.avg_latency_ms == 30.0
    assert metrics.p50_latency_ms == 30.0
    assert metrics.p95_latency_ms == 50.0

@pytest.mark.asyncio
async def test_global_stats(optimizer):
    optimizer.record_request("m1", True, 100)
    optimizer.record_request("m2", False, 200)

    stats = optimizer.get_global_stats()
    assert stats["total_requests"] == 2
    assert stats["active_models"] == 2
    assert stats["avg_latency_ms"] == 150.0
