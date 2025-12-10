# app/services/serving/application/inference_router.py
"""
Inference Router Service
=========================
Routes inference requests to appropriate models.

Single Responsibility: Request routing and execution orchestration.
"""

from __future__ import annotations

import logging
import uuid

from app.services.serving.domain.models import (
    ModelRequest,
    ModelResponse,
    ModelStatus,
)
from app.services.serving.application.model_registry import ModelRegistry
from app.services.serving.infrastructure.mock_model_invoker import MockModelInvoker
from app.services.serving.infrastructure.in_memory_repository import (
    InMemoryMetricsRepository,
)

_LOG = logging.getLogger(__name__)


class InferenceRouter:
    """
    Routes and executes inference requests.
    
    Responsibilities:
    - Route requests to appropriate model versions
    - Execute inference via model invoker
    - Track request/response history
    - Update metrics
    
    Does NOT handle:
    - Model lifecycle (ModelRegistry)
    - A/B testing logic (ExperimentManager)
    - Cost calculation (CostCalculator)
    """

    def __init__(
        self,
        registry: ModelRegistry,
        invoker: MockModelInvoker | None = None,
        metrics_repo: InMemoryMetricsRepository | None = None,
    ):
        """
        Initialize inference router.
        
        Args:
            registry: Model registry for model lookup
            invoker: Model invoker for actual inference
            metrics_repo: Metrics repository for tracking
        """
        self._registry = registry
        self._invoker = invoker or MockModelInvoker()
        self._metrics_repo = metrics_repo or InMemoryMetricsRepository()

    def serve_request(
        self,
        model_name: str,
        input_data: dict,
        version_id: str | None = None,
        parameters: dict | None = None,
    ) -> ModelResponse:
        """
        Serve an inference request.
        
        Args:
            model_name: Name of the model
            input_data: Input data for inference
            version_id: Optional specific version ID
            parameters: Optional request parameters
            
        Returns:
            Model response with results or error
        """
        request_id = str(uuid.uuid4())

        # Select model version
        if version_id:
            model = self._registry.get_model(version_id)
        else:
            model = self._registry.get_latest_ready_model(model_name)

        # Validate model availability
        if not model:
            return ModelResponse(
                request_id=request_id,
                model_id=model_name,
                version_id=version_id or "unknown",
                output_data=None,
                latency_ms=0.0,
                success=False,
                error=f"Model '{model_name}' not found or not ready",
            )

        if model.status != ModelStatus.READY:
            return ModelResponse(
                request_id=request_id,
                model_id=model.model_name,
                version_id=model.version_id,
                output_data=None,
                latency_ms=0.0,
                success=False,
                error=f"Model not ready (status: {model.status.value})",
            )

        # Create request object
        request = ModelRequest(
            request_id=request_id,
            model_id=model.model_name,
            version_id=model.version_id,
            input_data=input_data,
            parameters=parameters or {},
        )

        # Execute inference
        try:
            response = self._invoker.invoke(model, request)
            
            # Log success
            if response.success:
                _LOG.debug(
                    f"Request {request_id} completed: "
                    f"{response.latency_ms:.2f}ms, "
                    f"{response.tokens_used} tokens"
                )
            else:
                _LOG.warning(
                    f"Request {request_id} failed: {response.error}"
                )
            
            return response

        except Exception as e:
            _LOG.error(f"Inference error for request {request_id}: {e}")
            return ModelResponse(
                request_id=request_id,
                model_id=model.model_name,
                version_id=model.version_id,
                output_data=None,
                latency_ms=0.0,
                success=False,
                error=f"Inference failed: {str(e)}",
            )
