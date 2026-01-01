"""
Model Invoker
=============
Handles the actual invocation of models and request processing.
"""
from __future__ import annotations

import random
import time
import uuid
from collections import deque
from typing import Any

from app.services.serving.domain.models import (
    ModelRequest,
    ModelResponse,
    ModelStatus,
    ModelType,
    ModelVersion,
)


class ModelInvoker:
    """
    Model Invoker - منفذ النماذج

    Responsibilities:
    - Execute model inference
    - Track request/response history
    - Handle model invocation errors
    """

    def __init__(self):
        self._request_history: deque[ModelRequest] = deque(maxlen=10000)
        self._response_history: deque[ModelResponse] = deque(maxlen=10000)

    def serve_request(self, model: ModelVersion, input_data: dict[str, Any],
        parameters: (dict[str, Any] | None)=None, cost_calculator: (
        callable | None)=None, metrics_updater: (callable | None)=None
        ) ->ModelResponse:
        """
        خدمة طلب للنموذج

        Args:
            model: نسخة النموذج
            input_data: بيانات الإدخال
            parameters: معاملات الطلب
            cost_calculator: دالة لحساب التكلفة
            metrics_updater: دالة لتحديث المقاييس

        Returns:
            استجابة النموذج
        """
        request_id = str(uuid.uuid4())
        if model.status != ModelStatus.READY:
            return ModelResponse(request_id=request_id, model_id=model.
                model_name, version_id=model.version_id, output_data=None,
                latency_ms=0, success=False, error='Model not ready')
        request = ModelRequest(request_id=request_id, model_id=model.
            model_name, version_id=model.version_id, input_data=input_data,
            parameters=parameters or {})
        self._request_history.append(request)
        start_time = time.time()
        try:
            output = self._invoke_model(model, input_data, parameters or {})
            latency_ms = (time.time() - start_time) * 1000
            cost = 0.0
            if cost_calculator:
                cost = cost_calculator(model, output)
            response = ModelResponse(request_id=request_id, model_id=model.
                model_name, version_id=model.version_id, output_data=output,
                latency_ms=latency_ms, tokens_used=len(str(input_data)) +
                len(str(output)), cost_usd=cost, success=True)
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            response = ModelResponse(request_id=request_id, model_id=model.
                model_name, version_id=model.version_id, output_data=None,
                latency_ms=latency_ms, success=False, error=str(e))
        self._response_history.append(response)
        if metrics_updater:
            metrics_updater(model.version_id, response)
        return response

    def _invoke_model(self, model: ModelVersion, input_data: dict[str, Any],
        parameters: dict[str, Any]) ->dict[str, str | int | bool]:
        """
        استدعاء النموذج الفعلي

        في النظام الحقيقي:
        - يتم استدعاء API الفعلي للنموذج
        - أو تشغيل النموذج محلياً

        هنا نحاكي العملية
        """
        time.sleep(random.uniform(0.1, 0.5))
        if model.model_type == ModelType.LANGUAGE_MODEL:
            return {'text':
                f"Generated response for: {input_data.get('prompt', '')}",
                'model': model.model_name, 'version': model.version_number}
        return {'result': 'processed', 'model': model.model_name}
