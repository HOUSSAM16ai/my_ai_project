# tests/phase3_refactoring/test_model_serving_refactored.py
"""
Tests for Refactored Model Serving Infrastructure
==================================================
Validates that the layered architecture works correctly.

Phase 3 Wave 1 - Verification Tests
"""

import time

import pytest

from app.services.serving import (
    InferenceRouter,
    # Infrastructure
    InMemoryModelRepository,
    MockModelInvoker,
    # Application services
    ModelRegistry,
    ModelStatus,
    ModelType,
    # Domain models
    ModelVersion,
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




if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
