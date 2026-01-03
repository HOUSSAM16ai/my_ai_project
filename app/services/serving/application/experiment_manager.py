# app/services/serving/application/experiment_manager.py
"""
Experiment Manager Service
===========================
Manages A/B tests, shadow deployments, and ensemble serving.

Single Responsibility: Experimental deployment strategies.
"""

from __future__ import annotations

from typing import Any


import logging
import random
import threading
import time
import uuid
from datetime import UTC, datetime

from app.services.serving.application.inference_router import InferenceRouter
from app.services.serving.application.model_registry import ModelRegistry
from app.services.serving.domain.models import (
    ABTestConfig,
    EnsembleConfig,
    ModelResponse,
    ShadowDeployment,
)

_LOG = logging.getLogger(__name__)

class ExperimentManager:
    """
    Manages experimental model serving strategies.

    Responsibilities:
    - A/B test creation and management
    - Shadow deployment orchestration
    - Ensemble serving coordination
    - Experiment analysis and reporting

    Does NOT handle:
    - Model loading (ModelRegistry)
    - Actual inference (InferenceRouter)
    - Metrics storage (MetricsRepository)
    """

    def __init__(
        self,
        registry: ModelRegistry,
        router: InferenceRouter,
    ):
        """
        Initialize experiment manager.

        Args:
            registry: Model registry for model lookup
            router: Inference router for execution
        """
        self._registry = registry
        self._router = router
        self._ab_tests: dict[str, ABTestConfig] = {}
        self._shadow_deployments: dict[str, ShadowDeployment] = {}
        self._ensembles: dict[str, EnsembleConfig] = {}
        self._lock = threading.RLock()

    # ======================================================================================
    # A/B TESTING
    # ======================================================================================

    def start_ab_test(
        self,
        model_a_id: str,
        model_b_id: str,
        split_percentage: float = 50.0,
        duration_hours: int = 24,
        success_metric: str = "latency",
    ) -> str:
        """
        بدء اختبار A/B بين نموذجين.
        Start an A/B test between two models.

        Args:
            model_a_id: معرف النموذج A | Model A version ID
            model_b_id: معرف النموذج B | Model B version ID
            split_percentage: نسبة الحركة للنموذج A (0-100) | Traffic percentage for model A
            duration_hours: مدة الاختبار بالساعات | Test duration in hours
            success_metric: المقياس للتحسين | Metric to optimize (latency, cost, accuracy)

        Returns:
            str: معرف الاختبار | Test ID
        """
        test_id = str(uuid.uuid4())
        config = self._create_ab_test_config(
            test_id, model_a_id, model_b_id, split_percentage, duration_hours, success_metric
        )
        
        self._register_ab_test(test_id, config)
        self._log_ab_test_start(test_id, model_a_id, model_b_id, split_percentage)
        self._schedule_auto_end(test_id, duration_hours)

        return test_id

    def _create_ab_test_config(
        self,
        test_id: str,
        model_a_id: str,
        model_b_id: str,
        split_percentage: float,
        duration_hours: int,
        success_metric: str,
    ) -> ABTestConfig:
        """
        إنشاء تكوين اختبار A/B.
        Create A/B test configuration.
        
        Args:
            test_id: معرف الاختبار | Test ID
            model_a_id: معرف النموذج A | Model A ID
            model_b_id: معرف النموذج B | Model B ID
            split_percentage: نسبة الحركة | Traffic percentage
            duration_hours: مدة الاختبار | Test duration
            success_metric: مقياس النجاح | Success metric
            
        Returns:
            ABTestConfig: تكوين الاختبار | Test configuration
        """
        return ABTestConfig(
            test_id=test_id,
            model_a_id=model_a_id,
            model_b_id=model_b_id,
            model_a_percentage=split_percentage,
            model_b_percentage=100.0 - split_percentage,
            duration_hours=duration_hours,
            success_metric=success_metric,
        )

    def _register_ab_test(self, test_id: str, config: ABTestConfig) -> None:
        """
        تسجيل اختبار A/B.
        Register A/B test.
        
        Args:
            test_id: معرف الاختبار | Test ID
            config: تكوين الاختبار | Test configuration
        """
        with self._lock:
            self._ab_tests[test_id] = config

    def _log_ab_test_start(
        self, 
        test_id: str, 
        model_a_id: str, 
        model_b_id: str, 
        split_percentage: float
    ) -> None:
        """
        تسجيل بدء اختبار A/B.
        Log A/B test start.
        
        Args:
            test_id: معرف الاختبار | Test ID
            model_a_id: معرف النموذج A | Model A ID
            model_b_id: معرف النموذج B | Model B ID
            split_percentage: نسبة الحركة | Traffic percentage
        """
        _LOG.info(
            f"Started A/B test {test_id}: "
            f"{model_a_id} ({split_percentage}%) vs "
            f"{model_b_id} ({100-split_percentage}%)"
        )

    def _schedule_auto_end(self, test_id: str, duration_hours: int) -> None:
        """
        جدولة إنهاء تلقائي للاختبار.
        Schedule automatic test end.
        
        Args:
            test_id: معرف الاختبار | Test ID
            duration_hours: مدة الاختبار بالساعات | Test duration in hours
        """
        threading.Thread(
            target=self._auto_end_test,
            args=(test_id, duration_hours),
            daemon=True,
        ).start()

    def serve_ab_test_request(
        self,
        test_id: str,
        input_data: dict,
        parameters: dict | None = None,
    ) -> ModelResponse:
        """
        تقديم طلب ضمن اختبار A/B.
        Serve request within an A/B test.

        Randomly routes to model A or B based on configured percentages.

        Args:
            test_id: معرف اختبار A/B | A/B test ID
            input_data: بيانات الإدخال | Input data
            parameters: معاملات اختيارية | Optional parameters

        Returns:
            ModelResponse: استجابة النموذج | Model response
        """
        config = self._get_ab_test_config(test_id)
        version_id = self._select_model_for_ab_test(config)
        model = self._get_model_by_version(version_id)
        
        return self._router.serve_request(
            model.model_name,
            input_data,
            version_id=version_id,
            parameters=parameters,
        )

    def _get_ab_test_config(self, test_id: str) -> ABTestConfig:
        """
        الحصول على تكوين اختبار A/B.
        Get A/B test configuration.
        
        Args:
            test_id: معرف الاختبار | Test ID
            
        Returns:
            ABTestConfig: تكوين الاختبار | Test configuration
            
        Raises:
            ValueError: إذا لم يُعثر على الاختبار | If test not found
        """
        config = self._ab_tests.get(test_id)
        if not config:
            raise ValueError(f"A/B test {test_id} not found")
        return config

    def _select_model_for_ab_test(self, config: ABTestConfig) -> str:
        """
        اختيار نموذج بناءً على نسبة الحركة.
        Select model based on traffic percentage.
        
        Args:
            config: تكوين اختبار A/B | A/B test config
            
        Returns:
            str: معرف النموذج المختار | Selected model version ID
        """
        if random.uniform(0, 100) < config.model_a_percentage:
            return config.model_a_id
        return config.model_b_id

    def _get_model_by_version(self, version_id: str):
        """
        الحصول على نموذج بواسطة معرف الإصدار.
        Get model by version ID.
        
        Args:
            version_id: معرف الإصدار | Version ID
            
        Returns:
            Model: كائن النموذج | Model object
            
        Raises:
            ValueError: إذا لم يُعثر على النموذج | If model not found
        """
        model = self._registry.get_model(version_id)
        if not model:
            raise ValueError(f"Model {version_id} not found")
        return model

    def analyze_ab_test(self, test_id: str) -> dict[str, Any]:
        """
        Analyze A/B test results and determine winner.

        Args:
            test_id: Test ID

        Returns:
            Analysis results with winner determination
        """
        config = self._ab_tests.get(test_id)
        if not config:
            return {"error": "Test not found"}

        # Get metrics for both models
        from app.services.serving.infrastructure.in_memory_repository import (
            InMemoryMetricsRepository,
        )
        metrics_repo = InMemoryMetricsRepository()

        metrics_a = metrics_repo.get_summary(config.model_a_id)
        metrics_b = metrics_repo.get_summary(config.model_b_id)

        # Determine winner based on success metric
        winner = self._determine_winner(config.success_metric, metrics_a, metrics_b)

        with self._lock:
            config.winner = winner
            config.ended_at = datetime.now(UTC)

        _LOG.info(f"A/B test {test_id} completed. Winner: Model {winner}")

        return {
            "test_id": test_id,
            "winner": winner,
            "model_a_metrics": metrics_a,
            "model_b_metrics": metrics_b,
            "duration_hours": (
                (datetime.now(UTC) - config.started_at).total_seconds() / 3600
            ),
        }

    def _determine_winner(
        self,
        metric: str,
        metrics_a: dict,
        metrics_b: dict,
    ) -> str:
        """Determine winner based on success metric"""
        if metric == "latency":
            return "A" if metrics_a["avg_latency"] < metrics_b["avg_latency"] else "B"
        if metric == "cost":
            return "A" if metrics_a["total_cost"] < metrics_b["total_cost"] else "B"
        if metric == "accuracy":
            return "A" if metrics_a["success_rate"] > metrics_b["success_rate"] else "B"
        return "A"  # Default

    def _auto_end_test(self, test_id: str, duration_hours: int) -> None:
        """Automatically end test after duration"""
        time.sleep(duration_hours * 3600)
        try:
            self.analyze_ab_test(test_id)
        except Exception as e:
            _LOG.error(f"Failed to auto-end test {test_id}: {e}")

    # ======================================================================================
    # SHADOW DEPLOYMENT
    # ======================================================================================

    def start_shadow_deployment(
        self,
        primary_model_id: str,
        shadow_model_id: str,
        traffic_percentage: float = 100.0,
    ) -> str:
        """
        بدء نشر ظل لاختبار نموذج جديد.
        Start shadow deployment for testing new model.

        Args:
            primary_model_id: معرف نموذج الإنتاج | Production model ID
            shadow_model_id: معرف نموذج الظل (قيد الاختبار) | Shadow model ID (being tested)
            traffic_percentage: نسبة الطلبات للظل (0-100) | % of requests to shadow

        Returns:
            str: معرف نشر الظل | Shadow deployment ID
        """
        shadow_id = str(uuid.uuid4())
        deployment = self._create_shadow_deployment(
            shadow_id, primary_model_id, shadow_model_id, traffic_percentage
        )
        
        self._register_shadow_deployment(shadow_id, deployment)
        self._log_shadow_deployment_start(shadow_id, shadow_model_id, primary_model_id)

        return shadow_id

    def _create_shadow_deployment(
        self,
        shadow_id: str,
        primary_model_id: str,
        shadow_model_id: str,
        traffic_percentage: float,
    ) -> ShadowDeployment:
        """
        إنشاء نشر ظل.
        Create shadow deployment.
        
        Args:
            shadow_id: معرف الظل | Shadow ID
            primary_model_id: معرف النموذج الأساسي | Primary model ID
            shadow_model_id: معرف نموذج الظل | Shadow model ID
            traffic_percentage: نسبة الحركة | Traffic percentage
            
        Returns:
            ShadowDeployment: نشر الظل | Shadow deployment
        """
        return ShadowDeployment(
            shadow_id=shadow_id,
            primary_model_id=primary_model_id,
            shadow_model_id=shadow_model_id,
            traffic_percentage=traffic_percentage,
        )

    def _register_shadow_deployment(self, shadow_id: str, deployment: ShadowDeployment) -> None:
        """
        تسجيل نشر الظل.
        Register shadow deployment.
        
        Args:
            shadow_id: معرف الظل | Shadow ID
            deployment: نشر الظل | Shadow deployment
        """
        with self._lock:
            self._shadow_deployments[shadow_id] = deployment

    def _log_shadow_deployment_start(
        self, 
        shadow_id: str, 
        shadow_model_id: str, 
        primary_model_id: str
    ) -> None:
        """
        تسجيل بدء نشر الظل.
        Log shadow deployment start.
        
        Args:
            shadow_id: معرف الظل | Shadow ID
            shadow_model_id: معرف نموذج الظل | Shadow model ID
            primary_model_id: معرف النموذج الأساسي | Primary model ID
        """
        _LOG.info(
            f"Started shadow deployment {shadow_id}: "
            f"{shadow_model_id} shadowing {primary_model_id}"
        )

    def get_ab_test(self, test_id: str) -> ABTestConfig | None:
        """Get A/B test configuration"""
        return self._ab_tests.get(test_id)

    def get_shadow_deployment(self, shadow_id: str) -> ShadowDeployment | None:
        """Get shadow deployment configuration"""
        return self._shadow_deployments.get(shadow_id)
