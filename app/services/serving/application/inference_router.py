# app/services/serving/application/inference_router.py
"""
خدمة موجه الاستدلال (Inference Router Service).

تقوم بتوجيه طلبات الاستدلال إلى نماذج الذكاء الاصطناعي المناسبة وتنفيذها.

المسؤوليات:
- توجيه الطلبات إلى إصدار النموذج الصحيح.
- تنفيذ الاستدلال عبر `ModelInvoker`.
- تتبع الاستجابات والمقاييس.

المعايير:
- Strict Typing (Python 3.12+).
- Arabic Docstrings.
"""

from __future__ import annotations

import logging
import uuid
from typing import TYPE_CHECKING

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

if TYPE_CHECKING:
    from app.services.serving.domain.models import AIModel

_LOG = logging.getLogger(__name__)


class InferenceRouter:
    """
    تدير وتوجه طلبات الاستدلال.
    """

    def __init__(
        self,
        registry: ModelRegistry,
        invoker: MockModelInvoker | None = None,
        metrics_repo: InMemoryMetricsRepository | None = None,
    ) -> None:
        """
        تهيئة موجه الاستدلال.

        Args:
            registry: سجل النماذج للبحث.
            invoker: منفذ الاستدلال (الفعلي أو الوهمي).
            metrics_repo: مستودع المقاييس للتتبع.
        """
        self._registry = registry
        self._invoker = invoker or MockModelInvoker()
        self._metrics_repo = metrics_repo or InMemoryMetricsRepository()

    def serve_request(
        self,
        model_name: str,
        input_data: dict[str, object],
        version_id: str | None = None,
        parameters: dict[str, object] | None = None,
    ) -> ModelResponse:
        """
        خدمة طلب استدلال.

        تقوم بتوجيه الطلب إلى النموذج المناسب وتنفيذ الاستدلال.

        Args:
            model_name: اسم النموذج.
            input_data: بيانات الإدخال.
            version_id: معرف الإصدار الاختياري.
            parameters: معاملات الطلب الاختيارية.

        Returns:
            ModelResponse: استجابة النموذج مع النتائج أو الخطأ.
        """
        request_id = str(uuid.uuid4())

        # 1. Select and validate model
        model = self._select_model(model_name, version_id)
        error_response = self._validate_model(model, model_name, version_id, request_id)
        if error_response:
            return error_response

        # Ensure model is not None (validated above)
        assert model is not None

        # 2. Create and execute request
        request = self._create_request(request_id, model, input_data, parameters)
        return self._execute_inference(request, model, request_id)

    def _select_model(self, model_name: str, version_id: str | None) -> AIModel | None:
        """
        اختيار إصدار النموذج المناسب.

        Args:
            model_name: اسم النموذج.
            version_id: معرف الإصدار (اختياري).

        Returns:
            AIModel | None: النموذج المحدد أو None.
        """
        if version_id:
            return self._registry.get_model(version_id)
        return self._registry.get_latest_ready_model(model_name)

    def _validate_model(
        self, model: AIModel | None, model_name: str, version_id: str | None, request_id: str
    ) -> ModelResponse | None:
        """
        التحقق من توفر وحالة النموذج.

        Args:
            model: النموذج للتحقق منه.
            model_name: اسم النموذج.
            version_id: معرف الإصدار.
            request_id: معرف الطلب.

        Returns:
            ModelResponse | None: استجابة خطأ أو None إذا كان صالحاً.
        """
        if not model:
            return self._create_error_response(
                request_id=request_id,
                model_id=model_name,
                version_id=version_id or "unknown",
                error=f"Model '{model_name}' not found or not ready",
            )

        if model.status != ModelStatus.READY:
            return self._create_error_response(
                request_id=request_id,
                model_id=model.model_name,
                version_id=model.version_id,
                error=f"Model not ready (status: {model.status.value})",
            )

        return None

    def _create_error_response(
        self, request_id: str, model_id: str, version_id: str, error: str
    ) -> ModelResponse:
        """
        إنشاء استجابة خطأ معيارية.

        Args:
            request_id: معرف الطلب.
            model_id: معرف النموذج.
            version_id: معرف الإصدار.
            error: رسالة الخطأ.

        Returns:
            ModelResponse: استجابة الخطأ.
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
        model: AIModel,
        input_data: dict[str, object],
        parameters: dict[str, object] | None,
    ) -> ModelRequest:
        """
        إنشاء كائن الطلب.

        Args:
            request_id: معرف الطلب.
            model: النموذج.
            input_data: بيانات الإدخال.
            parameters: المعاملات.

        Returns:
            ModelRequest: كائن الطلب.
        """
        return ModelRequest(
            request_id=request_id,
            model_id=model.model_name,
            version_id=model.version_id,
            input_data=input_data,
            parameters=parameters or {},
        )

    def _execute_inference(
        self, request: ModelRequest, model: AIModel, request_id: str
    ) -> ModelResponse:
        """
        تنفيذ عملية الاستدلال.

        Args:
            request: كائن الطلب.
            model: النموذج.
            request_id: معرف الطلب.

        Returns:
            ModelResponse: استجابة النموذج.
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
                error=f"Inference failed: {e!s}",
            )

    def _log_inference_result(self, request_id: str, response: ModelResponse) -> None:
        """
        تسجيل نتيجة الاستدلال.

        Args:
            request_id: معرف الطلب.
            response: استجابة النموذج.
        """
        if response.success:
            _LOG.debug(
                f"Request {request_id} completed: "
                f"{response.latency_ms:.2f}ms, "
                f"{response.tokens_used} tokens"
            )
        else:
            _LOG.warning(f"Request {request_id} failed: {response.error}")
