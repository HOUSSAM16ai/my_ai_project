# tests/phase3_refactoring/test_model_serving_refactored.py
"""
Tests for Refactored Model Serving Infrastructure
==================================================
Validates that the layered architecture works correctly.

Phase 3 Wave 1 - Verification Tests
"""

import pytest
import time
from datetime import datetime

from app.services.serving import (
    # Domain models
    ModelVersion,
    ModelStatus,
    ModelType,
    # Application services
    ModelRegistry,
    InferenceRouter,
    ExperimentManager,
    # Infrastructure
    InMemoryModelRepository,
    MockModelInvoker,
    # Facade (backward compatibility)
    ModelServingInfrastructure,
    get_model_serving_infrastructure,
)


class TestDomainLayer:
    """Test pure domain entities"""

    def test_model_version_creation(self):
        """Domain entities should be pure and testable"""
        model = ModelVersion(
            version_id="v1",
            model_name="gpt-4",
            version_number="1.0.0",
            model_type=ModelType.LANGUAGE_MODEL,
            status=ModelStatus.LOADING,
        )

        assert model.version_id == "v1"
        assert model.model_name == "gpt-4"
        assert model.status == ModelStatus.LOADING
        assert model.model_type == ModelType.LANGUAGE_MODEL

    def test_model_status_enum(self):
        """Enums should have expected values"""
        assert ModelStatus.LOADING.value == "loading"
        assert ModelStatus.READY.value == "ready"
        assert ModelStatus.STOPPED.value == "stopped"


class TestInfrastructureLayer:
    """Test infrastructure implementations"""

    def test_in_memory_repository_save_and_get(self):
        """Repository should store and retrieve models"""
        repo = InMemoryModelRepository()

        model = ModelVersion(
            version_id="v1",
            model_name="test-model",
            version_number="1.0.0",
            model_type=ModelType.LANGUAGE_MODEL,
            status=ModelStatus.READY,
        )

        # Save
        assert repo.save(model) is True
        assert repo.save(model) is False  # Duplicate

        # Retrieve
        retrieved = repo.get("v1")
        assert retrieved is not None
        assert retrieved.version_id == "v1"
        assert retrieved.model_name == "test-model"

    def test_in_memory_repository_list_by_name(self):
        """Repository should list models by name"""
        repo = InMemoryModelRepository()

        # Create multiple versions
        for i in range(3):
            model = ModelVersion(
                version_id=f"v{i}",
                model_name="test-model",
                version_number=f"1.{i}.0",
                model_type=ModelType.LANGUAGE_MODEL,
                status=ModelStatus.READY,
            )
            repo.save(model)

        # List by name
        models = repo.list_by_name("test-model")
        assert len(models) == 3

    def test_mock_invoker_generates_response(self):
        """Mock invoker should generate valid responses"""
        from app.services.serving.domain.models import ModelRequest

        invoker = MockModelInvoker(simulate_latency=False)

        model = ModelVersion(
            version_id="v1",
            model_name="test-model",
            version_number="1.0.0",
            model_type=ModelType.LANGUAGE_MODEL,
            status=ModelStatus.READY,
        )

        request = ModelRequest(
            request_id="req1",
            model_id="test-model",
            version_id="v1",
            input_data={"prompt": "Hello"},
        )

        response = invoker.invoke(model, request)

        assert response.success is True
        assert response.output_data is not None
        assert response.latency_ms >= 0
        assert response.tokens_used > 0


class TestApplicationLayer:
    """Test application services"""

    def test_model_registry_registers_model(self):
        """ModelRegistry should register and track models"""
        repo = InMemoryModelRepository()
        registry = ModelRegistry(repo)

        model = ModelVersion(
            version_id="v1",
            model_name="test-model",
            version_number="1.0.0",
            model_type=ModelType.LANGUAGE_MODEL,
            status=ModelStatus.LOADING,
        )

        assert registry.register_model(model) is True
        assert registry.get_model("v1") is not None

    def test_model_registry_gets_latest_ready(self):
        """Registry should return latest READY model"""
        repo = InMemoryModelRepository()
        registry = ModelRegistry(repo)

        # Register multiple versions
        for i in range(3):
            model = ModelVersion(
                version_id=f"v{i}",
                model_name="test-model",
                version_number=f"1.{i}.0",
                model_type=ModelType.LANGUAGE_MODEL,
                status=ModelStatus.READY,
            )
            repo.save(model)

        latest = registry.get_latest_ready_model("test-model")
        assert latest is not None
        assert latest.version_number == "1.2.0"  # Latest

    def test_inference_router_serves_request(self):
        """InferenceRouter should route and execute requests"""
        repo = InMemoryModelRepository()
        registry = ModelRegistry(repo)
        invoker = MockModelInvoker(simulate_latency=False)
        router = InferenceRouter(registry, invoker)

        # Register a model
        model = ModelVersion(
            version_id="v1",
            model_name="test-model",
            version_number="1.0.0",
            model_type=ModelType.LANGUAGE_MODEL,
            status=ModelStatus.READY,
        )
        repo.save(model)

        # Serve request
        response = router.serve_request(
            model_name="test-model",
            input_data={"prompt": "Hello"},
        )

        assert response.success is True
        assert response.model_id == "test-model"
        assert response.output_data is not None


class TestFacadeBackwardCompatibility:
    """Test that facade maintains backward compatibility"""

    def test_facade_register_and_serve(self):
        """Facade should work exactly like original API"""
        infra = ModelServingInfrastructure()

        # Register model
        model = ModelVersion(
            version_id="v1",
            model_name="test-model",
            version_number="1.0.0",
            model_type=ModelType.LANGUAGE_MODEL,
            status=ModelStatus.LOADING,
        )

        assert infra.register_model(model) is True

        # Wait for async loading
        time.sleep(3)

        # Serve request
        response = infra.serve_request(
            model_name="test-model",
            input_data={"prompt": "test"},
        )

        assert response.success is True
        assert response.latency_ms >= 0

    def test_singleton_pattern(self):
        """Singleton should return same instance"""
        infra1 = get_model_serving_infrastructure()
        infra2 = get_model_serving_infrastructure()

        assert infra1 is infra2

    def test_facade_ab_testing(self):
        """A/B testing should work through facade"""
        infra = ModelServingInfrastructure()

        # Register two models
        model_a = ModelVersion(
            version_id="v1-a",
            model_name="model-a",
            version_number="1.0.0",
            model_type=ModelType.LANGUAGE_MODEL,
            status=ModelStatus.READY,
        )
        model_b = ModelVersion(
            version_id="v1-b",
            model_name="model-b",
            version_number="1.0.0",
            model_type=ModelType.LANGUAGE_MODEL,
            status=ModelStatus.READY,
        )

        infra.register_model(model_a)
        infra.register_model(model_b)
        time.sleep(3)  # Wait for loading

        # Start A/B test
        test_id = infra.start_ab_test(
            model_a_id="v1-a",
            model_b_id="v1-b",
            split_percentage=50.0,
        )

        assert test_id is not None
        assert len(test_id) > 0

        # Get test status
        config = infra.get_ab_test_status(test_id)
        assert config is not None
        assert config.model_a_id == "v1-a"
        assert config.model_b_id == "v1-b"


class TestEndToEndWorkflow:
    """End-to-end integration tests"""

    def test_complete_workflow(self):
        """Test complete model serving workflow"""
        # 1. Create infrastructure
        infra = ModelServingInfrastructure()

        # 2. Register model
        model = ModelVersion(
            version_id="v1",
            model_name="production-model",
            version_number="1.0.0",
            model_type=ModelType.LANGUAGE_MODEL,
            status=ModelStatus.LOADING,
        )
        assert infra.register_model(model) is True

        # 3. Check status
        status = infra.get_model_status("v1")
        assert status is not None
        assert status.status == ModelStatus.LOADING

        # 4. Wait for model to be ready
        time.sleep(3)
        status = infra.get_model_status("v1")
        assert status.status == ModelStatus.READY

        # 5. Serve request
        response = infra.serve_request(
            model_name="production-model",
            input_data={"prompt": "What is AI?"},
        )
        assert response.success is True
        assert response.model_id == "production-model"

        # 6. Unload model
        assert infra.unload_model("v1") is True

        # 7. Verify draining
        time.sleep(1)
        status = infra.get_model_status("v1")
        assert status.status == ModelStatus.DRAINING

        # 8. Wait for stopped
        time.sleep(6)
        status = infra.get_model_status("v1")
        assert status.status == ModelStatus.STOPPED


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
