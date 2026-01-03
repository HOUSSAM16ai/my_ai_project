"""
Model Invoker
=============
Handles the actual invocation of models and request processing.
"""
from __future__ import annotations

from typing import Any


import random
import time
import uuid
from collections import deque

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

    def serve_request(
        self,
        model: ModelVersion,
        input_data: dict[str, Any],
        parameters: dict[str, Any] | None = None,
        cost_calculator: callable | None = None,
        metrics_updater: callable | None = None
    ) -> ModelResponse:
        """
        خدمة طلب للنموذج | Serve model request
        
        تنفيذ طلب الاستدلال وحساب التكلفة والمقاييس
        Executes inference request and calculates cost and metrics

        Args:
            model: نسخة النموذج | Model version
            input_data: بيانات الإدخال | Input data
            parameters: معاملات الطلب | Request parameters
            cost_calculator: دالة لحساب التكلفة | Cost calculation function
            metrics_updater: دالة لتحديث المقاييس | Metrics update function

        Returns:
            استجابة النموذج | Model response
        """
        request_id = str(uuid.uuid4())
        
        # Validate model status
        if model.status != ModelStatus.READY:
            return self._create_error_response(request_id, model, 'Model not ready')
        
        # Create and store request
        request = self._create_request(request_id, model, input_data, parameters)
        self._request_history.append(request)
        
        # Execute inference
        response = self._execute_inference(request_id, model, input_data, parameters, cost_calculator)
        
        # Store response and update metrics
        self._response_history.append(response)
        if metrics_updater:
            metrics_updater(model.version_id, response)
        
        return response

    def _create_error_response(
        self,
        request_id: str,
        model: ModelVersion,
        error: str
    ) -> ModelResponse:
        """
        إنشاء استجابة خطأ | Create error response
        
        Args:
            request_id: معرف الطلب | Request ID
            model: النموذج | Model
            error: رسالة الخطأ | Error message
            
        Returns:
            استجابة الخطأ | Error response
        """
        return ModelResponse(
            request_id=request_id,
            model_id=model.model_name,
            version_id=model.version_id,
            output_data=None,
            latency_ms=0,
            success=False,
            error=error
        )

    def _create_request(
        self,
        request_id: str,
        model: ModelVersion,
        input_data: dict[str, Any],
        parameters: dict[str, Any] | None
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
            parameters=parameters or {}
        )

    def _execute_inference(
        self,
        request_id: str,
        model: ModelVersion,
        input_data: dict[str, Any],
        parameters: dict[str, Any] | None,
        cost_calculator: callable | None
    ) -> ModelResponse:
        """
        تنفيذ الاستدلال | Execute inference
        
        Args:
            request_id: معرف الطلب | Request ID
            model: النموذج | Model
            input_data: بيانات الإدخال | Input data
            parameters: المعاملات | Parameters
            cost_calculator: حاسب التكلفة | Cost calculator
            
        Returns:
            استجابة النموذج | Model response
        """
        start_time = time.time()
        
        try:
            output = self._invoke_model(model, input_data, parameters or {})
            latency_ms = (time.time() - start_time) * 1000
            
            # Calculate cost if calculator provided
            cost = cost_calculator(model, output) if cost_calculator else 0.0
            
            return ModelResponse(
                request_id=request_id,
                model_id=model.model_name,
                version_id=model.version_id,
                output_data=output,
                latency_ms=latency_ms,
                tokens_used=len(str(input_data)) + len(str(output)),
                cost_usd=cost,
                success=True
            )
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return ModelResponse(
                request_id=request_id,
                model_id=model.model_name,
                version_id=model.version_id,
                output_data=None,
                latency_ms=latency_ms,
                success=False,
                error=str(e)
            )

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
