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

from app.services.serving.application.model_registry import ModelRegistry
from app.services.serving.domain.models import (
    ModelRequest,
    ModelResponse,
    ModelStatus,
)
from app.services.serving.infrastructure.in_memory_repository import (
    InMemoryMetricsRepository,
)
from app.services.serving.infrastructure.mock_model_invoker import MockModelInvoker

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
        خدمة طلب استدلال | Serve an inference request.
        
        توجيه الطلب إلى النموذج المناسب وتنفيذ الاستدلال
        Routes request to appropriate model and executes inference

        Args:
            model_name: اسم النموذج | Name of the model
            input_data: بيانات الإدخال | Input data for inference
            version_id: معرف الإصدار الاختياري | Optional specific version ID
            parameters: معاملات الطلب الاختيارية | Optional request parameters

        Returns:
            استجابة النموذج | Model response with results or error
        """
        request_id = str(uuid.uuid4())
        
        # Select and validate model
        model = self._select_model(model_name, version_id)
        error_response = self._validate_model(model, model_name, version_id, request_id)
        if error_response:
            return error_response
        
        # Create and execute request
        request = self._create_request(request_id, model, input_data, parameters)
        return self._execute_inference(request, model, request_id)

    def _select_model(self, model_name: str, version_id: str | None):
        """
        اختيار إصدار النموذج | Select model version
        
        Args:
            model_name: اسم النموذج | Model name
            version_id: معرف الإصدار | Version ID
            
        Returns:
            النموذج المحدد أو None | Selected model or None
        """
        if version_id:
            return self._registry.get_model(version_id)
        return self._registry.get_latest_ready_model(model_name)

    def _validate_model(
        self,
        model,
        model_name: str,
        version_id: str | None,
        request_id: str
    ) -> ModelResponse | None:
        """
        التحقق من توفر النموذج | Validate model availability
        
        Args:
            model: النموذج للتحقق | Model to validate
            model_name: اسم النموذج | Model name
            version_id: معرف الإصدار | Version ID
            request_id: معرف الطلب | Request ID
            
        Returns:
            استجابة خطأ أو None | Error response or None if valid
        """
        if not model:
            return self._create_error_response(
                request_id=request_id,
                model_id=model_name,
                version_id=version_id or "unknown",
                error=f"Model '{model_name}' not found or not ready"
            )
        
        if model.status != ModelStatus.READY:
            return self._create_error_response(
                request_id=request_id,
                model_id=model.model_name,
                version_id=model.version_id,
                error=f"Model not ready (status: {model.status.value})"
            )
        
        return None

    def _create_error_response(
        self,
        request_id: str,
        model_id: str,
        version_id: str,
        error: str
    ) -> ModelResponse:
        """
        إنشاء استجابة خطأ | Create error response
        
        Args:
            request_id: معرف الطلب | Request ID
            model_id: معرف النموذج | Model ID
            version_id: معرف الإصدار | Version ID
            error: رسالة الخطأ | Error message
            
        Returns:
            استجابة الخطأ | Error response
        """
        return ModelResponse(
            request_id=request_id,
            model_id=model_id,
            version_id=version_id,
            output_data=None,
            latency_ms=0.0,
            success=False,
            error=error,
        )

    def _create_request(
        self,
        request_id: str,
        model,
        input_data: dict,
        parameters: dict | None
    ) -> ModelRequest:
        """
        إنشاء كائن الطلب | Create request object
        
        Args:
            request_id: معرف الطلب | Request ID
            model: النموذج | Model
            input_data: بيانات الإدخال | Input data
            parameters: المعاملات | Parameters
            
        Returns:
            كائن الطلب | Request object
        """
        return ModelRequest(
            request_id=request_id,
            model_id=model.model_name,
            version_id=model.version_id,
            input_data=input_data,
            parameters=parameters or {},
        )

    def _execute_inference(
        self,
        request: ModelRequest,
        model,
        request_id: str
    ) -> ModelResponse:
        """
        تنفيذ الاستدلال | Execute inference
        
        Args:
            request: كائن الطلب | Request object
            model: النموذج | Model
            request_id: معرف الطلب | Request ID
            
        Returns:
            استجابة النموذج | Model response
        """
        try:
            response = self._invoker.invoke(model, request)
            self._log_inference_result(request_id, response)
            return response
        except Exception as e:
            _LOG.error(f"Inference error for request {request_id}: {e}")
            return self._create_error_response(
                request_id=request_id,
                model_id=model.model_name,
                version_id=model.version_id,
                error=f"Inference failed: {e!s}"
            )

    def _log_inference_result(self, request_id: str, response: ModelResponse) -> None:
        """
        تسجيل نتيجة الاستدلال | Log inference result
        
        Args:
            request_id: معرف الطلب | Request ID
            response: استجابة النموذج | Model response
        """
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
