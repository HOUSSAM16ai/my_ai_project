# tests/phase3_refactoring/test_model_serving_e2e.py
"""
End-to-End Tests for Model Serving (InferenceRouter)
====================================================
This replaces the old Facade E2E tests.
It verifies that the new architecture (InferenceRouter -> ModelRegistry -> ModelInvoker)
works correctly from an end-user perspective.
"""

import pytest

from app.services.serving import (
    InferenceRouter,
    InMemoryModelRepository,
    MockModelInvoker,
    ModelRegistry,
    ModelStatus,
    ModelType,
    ModelVersion,
)


@pytest.fixture
def e2e_stack():
    """Setup a complete serving stack for E2E testing"""
    repo = InMemoryModelRepository()
    registry = ModelRegistry(repo)
    invoker = MockModelInvoker(simulate_latency=False)
    router = InferenceRouter(registry, invoker)
    return repo, registry, router

class TestModelServingE2E:
    """
    End-to-End verification of the serving pipeline.
    """

    def test_full_inference_lifecycle(self, e2e_stack):
        """
        Verifies: Register -> Load -> Serve -> Success
        """
        repo, registry, router = e2e_stack

        # 1. Register a new model
        # NOTE: ModelRegistry.register_model forces status to LOADING and starts a thread.
        # We need to manually set it to READY for the test to avoid race conditions/sleeping.
        model = ModelVersion(
            version_id="gpt-4-turbo-v1",
            model_name="gpt-4-turbo",
            version_number="1.0.0",
            model_type=ModelType.LANGUAGE_MODEL,
            # Status will be overwritten by register_model to LOADING
            status=ModelStatus.READY,
        )
        registry.register_model(model)

        # Force status to READY synchronously for the test
        # (Simulating that the async loader finished instantly)
        model.status = ModelStatus.READY
        repo.update(model)

        # 2. Verify model is available
        latest = registry.get_latest_ready_model("gpt-4-turbo")
        assert latest is not None
        assert latest.version_id == "gpt-4-turbo-v1"

        # 3. Serve a request
        response = router.serve_request(
            model_name="gpt-4-turbo",
            input_data={"prompt": "Hello world"},
        )

        # 4. Verify response
        assert response.success is True
        assert response.model_id == "gpt-4-turbo"
        assert response.output_data is not None
        assert response.latency_ms >= 0

    def test_routing_to_missing_model_fails_gracefully(self, e2e_stack):
        """
        Verifies that requesting a non-existent model returns a failure
        rather than crashing.
        """
        _repo, _registry, router = e2e_stack

        response = router.serve_request(
            model_name="non-existent-model",
            input_data={"prompt": "test"},
        )

        assert response.success is False
        assert "not found" in str(response.error).lower()

    def test_fallback_to_older_version_if_latest_not_ready(self, e2e_stack):
        """
        Verifies that if v1.1.0 is LOADING, it falls back to v1.0.0 which is READY.
        """
        repo, registry, router = e2e_stack

        # Register v1.0.0 (READY)
        v1 = ModelVersion(
            version_id="v1",
            model_name="test-model",
            version_number="1.0.0",
            model_type=ModelType.LANGUAGE_MODEL,
            status=ModelStatus.READY,
        )
        # Manually save to bypass "LOADING" status override of register_model
        repo.save(v1)

        # Register v1.1.0 (LOADING) via registry (so it becomes LOADING)
        v2 = ModelVersion(
            version_id="v2",
            model_name="test-model",
            version_number="1.1.0",
            model_type=ModelType.LANGUAGE_MODEL,
            status=ModelStatus.LOADING,
        )
        registry.register_model(v2)

        # Request model
        # Should pick v1 because v2 is not ready
        response = router.serve_request("test-model", {"p": "1"})

        assert response.success is True
        # Verify it served v1
        assert response.version_id == "v1"
