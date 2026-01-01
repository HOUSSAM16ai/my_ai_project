# app/services/serving/application/model_registry.py
"""
Model Registry Service
======================
Application service for managing model lifecycle.

Single Responsibility: Model registration, loading, and status management.
"""

from __future__ import annotations

import logging
import threading
import time
from datetime import UTC, datetime

from app.services.serving.domain.models import ModelStatus, ModelVersion
from app.services.serving.infrastructure.in_memory_repository import (
    InMemoryModelRepository,
)

_LOG = logging.getLogger(__name__)

class ModelRegistry:
    """
    Application service for model registration and lifecycle management.

    Responsibilities:
    - Register new models
    - Load/unload models
    - Track model status
    - Query model information

    Does NOT handle:
    - Inference execution (InferenceRouter)
    - Metrics collection (MetricsCollector)
    - A/B testing (ExperimentManager)
    """

    def __init__(self, repository: InMemoryModelRepository | None = None):
        """
        Initialize model registry.

        Args:
            repository: Model storage repository (defaults to in-memory)
        """
        self._repository = repository or InMemoryModelRepository()
        self._lock = threading.RLock()

    def register_model(self, model: ModelVersion) -> bool:
        """
        Register a new model version.

        Sets initial status to LOADING and starts async loading process.

        Args:
            model: Model version to register

        Returns:
            True if registration successful, False if already exists
        """
        with self._lock:
            # Set initial status
            model.status = ModelStatus.LOADING

            # Save to repository
            if not self._repository.save(model):
                _LOG.warning(f"Model {model.version_id} already registered")
                return False

            _LOG.info(f"Registered model {model.model_name} v{model.version_number}")

            # Start async loading
            threading.Thread(
                target=self._load_model_async,
                args=(model.version_id,),
                daemon=True,
            ).start()

            return True

    # TODO: Split this function (31 lines) - KISS principle
    def unload_model(self, version_id: str) -> bool:
        """
        Unload a model (graceful shutdown).

        Transitions to DRAINING status, then STOPPED after cooldown.

        Args:
            version_id: Model version ID

        Returns:
            True if unload initiated, False if model not found
        """
        with self._lock:
            model = self._repository.get(version_id)
            if not model:
                _LOG.warning(f"Model {version_id} not found for unload")
                return False

            # Set draining status
            model.status = ModelStatus.DRAINING
            self._repository.update(model)

            _LOG.info(f"Draining model {version_id}")

            # Start async draining process
            threading.Thread(
                target=self._drain_and_stop,
                args=(version_id,),
                daemon=True,
            ).start()

            return True

    def get_model(self, version_id: str) -> ModelVersion | None:
        """Get model by version ID"""
        return self._repository.get(version_id)

    def list_models(self, model_name: str | None = None) -> list[ModelVersion]:
        """
        List all models or models by name.

        Args:
            model_name: Optional filter by model name

        Returns:
            List of model versions
        """
        if model_name:
            return self._repository.list_by_name(model_name)
        return self._repository.list_all()

    def get_latest_ready_model(self, model_name: str) -> ModelVersion | None:
        """
        Get the latest READY version of a model.

        Args:
            model_name: Model name

        Returns:
            Latest ready model version, or None if none available
        """
        models = self._repository.list_by_name(model_name)
        ready_models = [m for m in models if m.status == ModelStatus.READY]

        if not ready_models:
            return None

        # Sort by creation date (newest first)
        ready_models.sort(key=lambda m: m.created_at, reverse=True)
        return ready_models[0]

    def _load_model_async(self, version_id: str) -> None:
        """
        Async model loading simulation.

        In real implementation, this would:
        - Download model weights
        - Initialize model on device
        - Run warmup inferences
        """
        try:
            # Simulate loading time
            time.sleep(2.0)

            with self._lock:
                model = self._repository.get(version_id)
                if model:
                    model.status = ModelStatus.READY
                    model.loaded_at = datetime.now(UTC)
                    self._repository.update(model)
                    _LOG.info(f"Model {version_id} loaded successfully")

        except Exception as e:
            _LOG.error(f"Failed to load model {version_id}: {e}")
            with self._lock:
                model = self._repository.get(version_id)
                if model:
                    model.status = ModelStatus.FAILED
                    self._repository.update(model)

    def _drain_and_stop(self, version_id: str) -> None:
        """
        Drain active requests and stop model.

        Waits for cooldown period before transitioning to STOPPED.
        """
        try:
            # Wait for active requests to complete
            time.sleep(5.0)  # Cooldown period

            with self._lock:
                model = self._repository.get(version_id)
                if model:
                    model.status = ModelStatus.STOPPED
                    self._repository.update(model)
                    _LOG.info(f"Model {version_id} stopped")

        except Exception as e:
            _LOG.error(f"Error during model drain {version_id}: {e}")
