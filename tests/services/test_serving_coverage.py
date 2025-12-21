import time
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from app.services.serving.application.ab_test_engine import ABTestEngine
from app.services.serving.application.ensemble_router import EnsembleRouter
from app.services.serving.application.experiment_manager import ExperimentManager
from app.services.serving.application.inference_router import InferenceRouter
from app.services.serving.application.model_invoker import ModelInvoker
from app.services.serving.application.model_registry import ModelRegistry
from app.services.serving.application.shadow_deployment import ShadowDeploymentManager
from app.services.serving.domain.models import (
    ABTestConfig,
    EnsembleConfig,
    ModelMetrics,
    ModelRequest,
    ModelResponse,
    ModelStatus,
    ModelType,
    ModelVersion,
    ShadowDeployment,
)
from app.services.serving.infrastructure.in_memory_repository import (
    InMemoryMetricsRepository,
    InMemoryModelRepository,
)
from app.services.serving.infrastructure.metrics_collector import MetricsCollector
from app.services.serving.infrastructure.mock_model_invoker import MockModelInvoker

# --- Fixtures ---

@pytest.fixture
def mock_registry():
    return MagicMock(spec=ModelRegistry)

@pytest.fixture
def model_version():
    return ModelVersion(
        version_id="v1",
        model_name="gpt-4",
        version_number="v1",
        model_type=ModelType.LANGUAGE_MODEL,
        status=ModelStatus.READY,
        parameters={},
        metadata={"description": "test", "file_path": "/tmp/model"}
    )

# --- ABTestEngine Tests ---

def test_ab_test_engine(mock_registry):
    engine = ABTestEngine(mock_registry)

    # Start Test
    test_id = engine.start_ab_test("model-a", "model-b", 60.0, duration_hours=1)
    assert test_id is not None

    # Check Status
    config = engine.get_ab_test_status(test_id)
    assert config is not None
    assert config.model_a_id == "model-a"
    assert config.model_a_percentage == 60.0
    assert config.model_b_percentage == 40.0

    # Analyze Test
    mock_metrics_getter = MagicMock(side_effect=lambda mid: {
        "avg_latency": 100 if mid == "model-a" else 200,
        "total_cost": 1.0
    })

    result = engine.analyze_ab_test(test_id, mock_metrics_getter)
    assert result["winner"] == "A" # Lower latency wins by default
    assert result["test_id"] == test_id

    # Test Not Found
    assert engine.analyze_ab_test("invalid", mock_metrics_getter) == {'error': 'Test not found'}
    assert engine.get_ab_test_status("invalid") is None

    # Test Cost Metric
    config.success_metric = "cost"
    mock_metrics_getter_cost = MagicMock(side_effect=lambda mid: {
        "avg_latency": 100,
        "total_cost": 2.0 if mid == "model-a" else 1.0
    })
    result_cost = engine.analyze_ab_test(test_id, mock_metrics_getter_cost)
    assert result_cost["winner"] == "B"

    # Test Default Metric
    config.success_metric = "unknown"
    result_default = engine.analyze_ab_test(test_id, mock_metrics_getter)
    assert result_default["winner"] == "A"


# --- EnsembleRouter Tests ---

def test_ensemble_router():
    router = EnsembleRouter()

    # Create Ensemble
    ensemble_id = router.create_ensemble(["m1", "m2", "m3"], "voting")
    assert ensemble_id is not None

    # Test Aggregations
    r1 = ModelResponse(request_id="1", model_id="m1", version_id="v1", output_data="yes", latency_ms=10, success=True, tokens_used=10, cost_usd=0.01)
    r2 = ModelResponse(request_id="1", model_id="m2", version_id="v1", output_data="yes", latency_ms=10, success=True, tokens_used=10, cost_usd=0.01)
    r3 = ModelResponse(request_id="1", model_id="m3", version_id="v1", output_data="no", latency_ms=10, success=True, tokens_used=10, cost_usd=0.01)
    r_fail = ModelResponse(request_id="1", model_id="m4", version_id="v1", output_data=None, latency_ms=0, success=False)

    # Voting
    assert router._voting_aggregation([r1, r2, r3, r_fail]) == "yes"
    assert router._voting_aggregation([r_fail]) is None

    # Averaging
    r_num1 = ModelResponse(request_id="1", model_id="m1", version_id="v1", output_data=10, latency_ms=10, success=True)
    r_num2 = ModelResponse(request_id="1", model_id="m2", version_id="v1", output_data=20, latency_ms=10, success=True)
    avg_res = router._averaging_aggregation([r_num1, r_num2])
    assert avg_res["averaged_results"] == [10, 20]

    # Default
    def_res = router._default_aggregation([r1, r3])
    assert def_res["ensemble_results"] == ["yes", "no"]

    # Create Response
    final = router.create_ensemble_response(ensemble_id, "yes", [r1, r2, r3], 30.0)
    assert final.success is True
    assert final.output_data == "yes"
    assert final.cost_usd == 0.03
    assert final.tokens_used == 30

# --- ModelInvoker Tests ---

def test_model_invoker(model_version):
    invoker = ModelInvoker()

    # Test Success (LLM)
    model_version.model_type = ModelType.LANGUAGE_MODEL
    resp = invoker.serve_request(model_version, {"prompt": "hello"})
    assert resp.success is True
    assert "Generated response" in resp.output_data["text"]

    # Test Success (Other)
    model_version.model_type = ModelType.VISION_MODEL
    resp = invoker.serve_request(model_version, {"image": "data"})
    assert resp.success is True
    assert resp.output_data["result"] == "processed"

    # Test Not Ready
    model_version.status = ModelStatus.FAILED
    resp = invoker.serve_request(model_version, {})
    assert resp.success is False
    assert resp.error == "Model not ready"

    # Test Exception during invoke
    model_version.status = ModelStatus.READY
    with patch.object(invoker, '_invoke_model', side_effect=Exception("Boom")):
        resp = invoker.serve_request(model_version, {})
        assert resp.success is False
        assert resp.error == "Boom"

    # Test Cost Calc & Metrics
    mock_calc = MagicMock(return_value=0.05)
    mock_updater = MagicMock()
    resp = invoker.serve_request(model_version, {"prompt": "hi"}, cost_calculator=mock_calc, metrics_updater=mock_updater)
    assert resp.cost_usd == 0.05
    mock_updater.assert_called_once()


# --- ShadowDeploymentManager Tests ---

def test_shadow_deployment_manager():
    manager = ShadowDeploymentManager()

    # Start
    sid = manager.start_shadow_deployment("p1", "s1")
    assert sid is not None

    # Stats (Empty)
    stats = manager.get_shadow_deployment_stats(sid)
    assert stats["message"] == "No comparisons yet"

    # Populate comparisons manually
    with manager._lock:
        manager._shadow_deployments[sid].comparison_results.append({
            "primary_latency": 100, "shadow_latency": 200, "primary_success": True, "shadow_success": True
        })
        manager._shadow_deployments[sid].comparison_results.append({
            "primary_latency": 300, "shadow_latency": 200, "primary_success": True, "shadow_success": True
        })

    stats = manager.get_shadow_deployment_stats(sid)
    assert stats["total_comparisons"] == 2
    assert stats["primary_faster_count"] == 1
    assert stats["shadow_faster_count"] == 1

    assert manager.get_shadow_deployment_stats("invalid") is None

# --- MetricsCollector Tests ---

def test_metrics_collector(model_version):
    collector = MetricsCollector()

    # Calculate Cost
    cost = collector.calculate_cost(model_version, {})
    assert cost >= 0.001

    # Update Metrics
    resp = ModelResponse(request_id="1", model_id="m", version_id="v", output_data="", latency_ms=10, success=True)
    collector.update_metrics("v", resp) # Should not crash

    # Get Metrics
    metrics = collector.get_all_metrics("v")
    assert isinstance(metrics, list)

    collector.collect_all_metrics() # Should not crash

# --- ModelRegistry Tests ---

def test_model_registry(model_version):
    registry = ModelRegistry() # Uses InMemoryModelRepository by default

    # Register
    assert registry.register_model(model_version) is True
    assert model_version.status == ModelStatus.LOADING

    # Duplicate Register
    assert registry.register_model(model_version) is False

    # List
    assert len(registry.list_models()) == 1
    assert len(registry.list_models("gpt-4")) == 1
    assert len(registry.list_models("other")) == 0

    # Get
    found = registry.get_model(model_version.version_id)
    assert found == model_version

    # Unload
    assert registry.unload_model(model_version.version_id) is True
    assert model_version.status == ModelStatus.DRAINING

    assert registry.unload_model("invalid") is False

    # Get Latest Ready
    # Mock status to READY for test
    model_version.status = ModelStatus.READY
    registry._repository.update(model_version)
    latest = registry.get_latest_ready_model("gpt-4")
    assert latest == model_version

    assert registry.get_latest_ready_model("other") is None

    # Async loading simulation (fast forward or mocked wait)
    # The registry starts a thread. We can sleep briefly or check logs if we had log capture.
    # Since we manually manipulated status above, let's just trust the thread logic is triggered.

# --- InferenceRouter Tests ---

def test_inference_router(model_version):
    registry = ModelRegistry()
    model_version.status = ModelStatus.READY
    registry.register_model(model_version)
    # Force ready status immediately avoiding thread race for test
    model_version.status = ModelStatus.READY
    registry._repository.update(model_version)

    router = InferenceRouter(registry)

    # Serve Request (Latest)
    resp = router.serve_request("gpt-4", {"prompt": "test"})
    assert resp.success is True

    # Serve Request (Specific Version)
    resp_v = router.serve_request("gpt-4", {"prompt": "test"}, version_id="v1")
    assert resp_v.success is True

    # Model Not Found
    resp_nf = router.serve_request("unknown", {})
    assert resp_nf.success is False
    assert "not found" in resp_nf.error

    # Model Not Ready
    model_version.status = ModelStatus.LOADING
    registry._repository.update(model_version)
    resp_nr = router.serve_request("gpt-4", {})
    assert resp_nr.success is False
    assert "not ready" in resp_nr.error

    # Invoker Error
    model_version.status = ModelStatus.READY
    registry._repository.update(model_version)
    with patch.object(router._invoker, 'invoke', side_effect=Exception("Fail")):
        resp_err = router.serve_request("gpt-4", {})
        assert resp_err.success is False
        assert "Inference failed" in resp_err.error

# --- InMemoryRepository Tests ---

def test_in_memory_repos(model_version):
    # Model Repo
    repo = InMemoryModelRepository()
    assert repo.save(model_version) is True
    assert repo.get(model_version.version_id) == model_version
    assert len(repo.list_all()) == 1
    assert repo.delete(model_version.version_id) is True
    assert repo.get(model_version.version_id) is None
    assert repo.update(model_version) is False # Deleted

    # Metrics Repo
    m_repo = InMemoryMetricsRepository()
    metric = ModelMetrics(version_id="v1", total_requests=10, successful_requests=10, avg_latency_ms=100.0, cost_usd=0.01)
    m_repo.record(metric)

    recent = m_repo.get_recent("v1")
    assert len(recent) == 1

    summary = m_repo.get_summary("v1")
    assert summary["total_requests"] == 10
    assert summary["success_rate"] == 100.0

    empty_summary = m_repo.get_summary("v2")
    assert empty_summary["total_requests"] == 0

# --- ExperimentManager Tests ---

def test_experiment_manager(model_version):
    registry = ModelRegistry()
    registry.register_model(model_version)
    model_version.status = ModelStatus.READY
    registry._repository.update(model_version)

    # Create a second model
    model_v2 = ModelVersion(
        version_id="v2",
        model_name="gpt-4",
        version_number="v2",
        model_type=ModelType.LANGUAGE_MODEL,
        status=ModelStatus.READY,
        parameters={},
        metadata={}
    )
    registry.register_model(model_v2)
    model_v2.status = ModelStatus.READY
    registry._repository.update(model_v2)

    router = InferenceRouter(registry)
    manager = ExperimentManager(registry, router)

    # Start A/B Test
    test_id = manager.start_ab_test("v1", "v2", 50.0)
    assert manager.get_ab_test(test_id) is not None

    # Serve Request
    resp = manager.serve_ab_test_request(test_id, {"prompt": "test"})
    assert resp.success is True

    # Test Not Found
    with pytest.raises(ValueError):
        manager.serve_ab_test_request("invalid", {})

    # Start Shadow
    shadow_id = manager.start_shadow_deployment("v1", "v2")
    assert manager.get_shadow_deployment(shadow_id) is not None

    # Analyze A/B (Mock metrics)
    with patch('app.services.serving.infrastructure.in_memory_repository.InMemoryMetricsRepository.get_summary') as mock_get:
        mock_get.side_effect = lambda vid: {
            "avg_latency": 100 if vid == "v1" else 200,
            "total_cost": 1.0,
            "success_rate": 100.0
        }
        res = manager.analyze_ab_test(test_id)
        assert res["winner"] == "A"

        # Test Not Found Analysis
        assert manager.analyze_ab_test("invalid") == {"error": "Test not found"}

    # Auto-end (Testing logic, not thread wait)
    # The auto_end thread runs time.sleep, skipping it for unit test speed.
    # But we can verify _auto_end_test logic safely:
    with patch.object(manager, 'analyze_ab_test') as mock_analyze:
        with patch('time.sleep'):
            manager._auto_end_test(test_id, 1)
            mock_analyze.assert_called_with(test_id)
