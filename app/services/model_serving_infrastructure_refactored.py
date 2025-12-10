# app/services/model_serving_infrastructure_refactored.py
# ======================================================================================
# ==    AI MODEL SERVING INFRASTRUCTURE - REFACTORED VERSION                         ==
# ======================================================================================
# This is the refactored version following SRP (Single Responsibility Principle).
# The original file is preserved as _legacy for reference.
#
# Refactoring follows the pattern established in app/ai/ and app/services/llm/

from __future__ import annotations

import threading
import time
from typing import Any

# Import refactored components
from app.serving.application import (
    ABTestEngine,
    EnsembleRouter,
    ModelInvoker,
    ModelRegistry,
    ShadowDeploymentManager,
)
from app.serving.domain.entities import (
    ABTestConfig,
    EnsembleConfig,
    ModelRequest,
    ModelResponse,
    ModelVersion,
    ShadowDeployment,
)
from app.serving.infrastructure import MetricsCollector


class ModelServingInfrastructure:
    """
    Model Serving Infrastructure Facade (Refactored)
    ================================================
    
    This is a thin facade that delegates to specialized components.
    Each component has a single responsibility (SRP).
    
    Architecture:
    - ModelRegistry: Model lifecycle management
    - ABTestEngine: A/B testing logic
    - ShadowDeploymentManager: Shadow deployment logic
    - EnsembleRouter: Ensemble routing logic
    - ModelInvoker: Model invocation logic
    - MetricsCollector: Metrics collection and monitoring
    
    This maintains backward compatibility with the original API.
    """

    def __init__(self):
        # Initialize specialized components
        self._registry = ModelRegistry()
        self._ab_test_engine = ABTestEngine(self._registry)
        self._shadow_manager = ShadowDeploymentManager()
        self._ensemble_router = EnsembleRouter()
        self._model_invoker = ModelInvoker()
        self._metrics = MetricsCollector()
        
        # Start performance monitoring
        self._metrics.start_performance_monitoring()

    # ======================================================================================
    # MODEL MANAGEMENT (Delegates to ModelRegistry)
    # ======================================================================================

    def register_model(self, model: ModelVersion) -> bool:
        """تسجيل نموذج جديد"""
        return self._registry.register_model(model)

    def unload_model(self, version_id: str) -> bool:
        """إلغاء تحميل نموذج"""
        return self._registry.unload_model(version_id)

    def get_model_status(self, version_id: str) -> ModelVersion | None:
        """الحصول على حالة النموذج"""
        return self._registry.get_model_status(version_id)

    def list_models(self) -> list[ModelVersion]:
        """قائمة بجميع النماذج المسجلة"""
        return self._registry.list_models()

    # ======================================================================================
    # MODEL SERVING (Delegates to ModelInvoker)
    # ======================================================================================

    def serve_request(
        self,
        model_name: str,
        input_data: dict[str, Any],
        version_id: str | None = None,
        parameters: dict[str, Any] | None = None,
    ) -> ModelResponse:
        """
        خدمة طلب للنموذج
        
        Args:
            model_name: اسم النموذج
            input_data: بيانات الإدخال
            version_id: معرف النسخة (اختياري)
            parameters: معاملات الطلب
            
        Returns:
            استجابة النموذج
        """
        # Get the model
        if version_id:
            model = self._registry.get_model(version_id)
        else:
            model = self._registry.get_latest_ready_model(model_name)

        if not model:
            import uuid
            return ModelResponse(
                request_id=str(uuid.uuid4()),
                model_id=model_name,
                version_id=version_id or "unknown",
                output_data=None,
                latency_ms=0,
                success=False,
                error="Model not found or not ready",
            )

        # Serve the request using ModelInvoker
        return self._model_invoker.serve_request(
            model=model,
            input_data=input_data,
            parameters=parameters,
            cost_calculator=self._metrics.calculate_cost,
            metrics_updater=self._metrics.update_metrics,
        )

    # ======================================================================================
    # A/B TESTING (Delegates to ABTestEngine)
    # ======================================================================================

    def start_ab_test(
        self,
        model_a_id: str,
        model_b_id: str,
        split_percentage: float = 50.0,
        duration_hours: int = 24,
    ) -> str:
        """بدء اختبار A/B بين نموذجين"""
        return self._ab_test_engine.start_ab_test(
            model_a_id, model_b_id, split_percentage, duration_hours
        )

    def serve_ab_test_request(
        self,
        test_id: str,
        input_data: dict[str, Any],
        parameters: dict[str, Any] | None = None,
    ) -> ModelResponse:
        """خدمة طلب ضمن اختبار A/B"""
        # Route to the selected model
        version_id = self._ab_test_engine.route_ab_test_request(test_id)
        model = self._registry.get_model(version_id)
        
        if not model:
            import uuid
            return ModelResponse(
                request_id=str(uuid.uuid4()),
                model_id="ab_test",
                version_id=test_id,
                output_data=None,
                latency_ms=0,
                success=False,
                error="Model not found in A/B test",
            )

        return self._model_invoker.serve_request(
            model=model,
            input_data=input_data,
            parameters=parameters,
            cost_calculator=self._metrics.calculate_cost,
            metrics_updater=self._metrics.update_metrics,
        )

    def analyze_ab_test(self, test_id: str) -> dict[str, Any]:
        """تحليل نتائج اختبار A/B وتحديد الفائز"""
        return self._ab_test_engine.analyze_ab_test(
            test_id, self._metrics.get_model_metrics_summary
        )

    def get_ab_test_status(self, test_id: str) -> ABTestConfig | None:
        """الحصول على حالة اختبار A/B"""
        return self._ab_test_engine.get_ab_test_status(test_id)

    # ======================================================================================
    # SHADOW MODE (Delegates to ShadowDeploymentManager)
    # ======================================================================================

    def start_shadow_deployment(
        self,
        primary_model_id: str,
        shadow_model_id: str,
        traffic_percentage: float = 100.0,
    ) -> str:
        """بدء نشر في الوضع الخفي (Shadow Mode)"""
        return self._shadow_manager.start_shadow_deployment(
            primary_model_id, shadow_model_id, traffic_percentage
        )

    def serve_with_shadow(
        self,
        shadow_id: str,
        input_data: dict[str, Any],
        parameters: dict[str, Any] | None = None,
    ) -> ModelResponse:
        """خدمة طلب مع نشر خفي"""
        deployment = self._shadow_manager.get_deployment(shadow_id)
        
        if not deployment:
            import uuid
            return ModelResponse(
                request_id=str(uuid.uuid4()),
                model_id="shadow",
                version_id=shadow_id,
                output_data=None,
                latency_ms=0,
                success=False,
                error=f"Shadow deployment {shadow_id} not found",
            )

        # Serve primary request
        primary_model = self._registry.get_model(deployment.primary_model_id)
        if not primary_model:
            import uuid
            return ModelResponse(
                request_id=str(uuid.uuid4()),
                model_id="shadow",
                version_id=shadow_id,
                output_data=None,
                latency_ms=0,
                success=False,
                error="Primary model not found",
            )

        primary_response = self._model_invoker.serve_request(
            model=primary_model,
            input_data=input_data,
            parameters=parameters,
            cost_calculator=self._metrics.calculate_cost,
            metrics_updater=self._metrics.update_metrics,
        )

        # Serve shadow request in background if needed
        if self._shadow_manager.should_shadow_request(shadow_id):
            def shadow_request():
                shadow_model = self._registry.get_model(deployment.shadow_model_id)
                if shadow_model:
                    shadow_response = self._model_invoker.serve_request(
                        model=shadow_model,
                        input_data=input_data,
                        parameters=parameters,
                        cost_calculator=self._metrics.calculate_cost,
                        metrics_updater=self._metrics.update_metrics,
                    )
                    self._shadow_manager.record_comparison(
                        shadow_id, primary_response, shadow_response
                    )

            threading.Thread(target=shadow_request, daemon=True).start()

        return primary_response

    def get_shadow_deployment_stats(self, shadow_id: str) -> dict[str, Any] | None:
        """الحصول على إحصائيات النشر الخفي"""
        return self._shadow_manager.get_shadow_deployment_stats(shadow_id)

    # ======================================================================================
    # ENSEMBLE SERVING (Delegates to EnsembleRouter)
    # ======================================================================================

    def create_ensemble(
        self,
        model_versions: list[str],
        aggregation_method: str = "voting",
        weights: dict[str, float] | None = None,
    ) -> str:
        """إنشاء تجميع نماذج (Ensemble)"""
        return self._ensemble_router.create_ensemble(
            model_versions, aggregation_method, weights
        )

    def serve_ensemble_request(
        self,
        ensemble_id: str,
        input_data: dict[str, Any],
        parameters: dict[str, Any] | None = None,
    ) -> ModelResponse:
        """خدمة طلب باستخدام تجميع نماذج"""
        config = self._ensemble_router.get_ensemble_config(ensemble_id)
        
        if not config:
            import uuid
            return ModelResponse(
                request_id=str(uuid.uuid4()),
                model_id="ensemble",
                version_id=ensemble_id,
                output_data=None,
                latency_ms=0,
                success=False,
                error=f"Ensemble {ensemble_id} not found",
            )

        start_time = time.time()

        # Invoke all models
        responses = []
        for version_id in config.model_versions:
            model = self._registry.get_model(version_id)
            if model:
                response = self._model_invoker.serve_request(
                    model=model,
                    input_data=input_data,
                    parameters=parameters,
                    cost_calculator=self._metrics.calculate_cost,
                    metrics_updater=self._metrics.update_metrics,
                )
                responses.append(response)

        # Aggregate responses
        aggregated_output = self._ensemble_router.aggregate_responses(
            responses, ensemble_id
        )

        total_latency = (time.time() - start_time) * 1000

        # Create ensemble response
        return self._ensemble_router.create_ensemble_response(
            ensemble_id, aggregated_output, responses, total_latency
        )


# ======================================================================================
# SINGLETON INSTANCE (Backward Compatibility)
# ======================================================================================

_model_serving_instance: ModelServingInfrastructure | None = None
_model_serving_lock = threading.Lock()


def get_model_serving_infrastructure() -> ModelServingInfrastructure:
    """الحصول على نسخة واحدة من بنية تقديم النماذج (Singleton)"""
    global _model_serving_instance

    if _model_serving_instance is None:
        with _model_serving_lock:
            if _model_serving_instance is None:
                _model_serving_instance = ModelServingInfrastructure()

    return _model_serving_instance
