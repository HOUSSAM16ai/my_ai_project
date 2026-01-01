# app/services/serving/application/experiment_manager.py
"""
Experiment Manager Service
===========================
Manages A/B tests, shadow deployments, and ensemble serving.

Single Responsibility: Experimental deployment strategies.
"""

from __future__ import annotations

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

    # TODO: Split this function (49 lines) - KISS principle
    # TODO: Reduce parameters (6 params) - Use config object
    def start_ab_test(
        self,
        model_a_id: str,
        model_b_id: str,
        split_percentage: float = 50.0,
        duration_hours: int = 24,
        success_metric: str = "latency",
    ) -> str:
        """
        Start an A/B test between two models.

        Args:
            model_a_id: Model A version ID
            model_b_id: Model B version ID
            split_percentage: Traffic percentage for model A (0-100)
            duration_hours: Test duration in hours
            success_metric: Metric to optimize (latency, cost, accuracy)

        Returns:
            Test ID
        """
        test_id = str(uuid.uuid4())

        config = ABTestConfig(
            test_id=test_id,
            model_a_id=model_a_id,
            model_b_id=model_b_id,
            model_a_percentage=split_percentage,
            model_b_percentage=100.0 - split_percentage,
            duration_hours=duration_hours,
            success_metric=success_metric,
        )

        with self._lock:
            self._ab_tests[test_id] = config

        _LOG.info(
            f"Started A/B test {test_id}: "
            f"{model_a_id} ({split_percentage}%) vs "
            f"{model_b_id} ({100-split_percentage}%)"
        )

        # Schedule automatic test end
        threading.Thread(
            target=self._auto_end_test,
            args=(test_id, duration_hours),
            daemon=True,
        ).start()

        return test_id
# TODO: Split this function (39 lines) - KISS principle

    def serve_ab_test_request(
        self,
        test_id: str,
        input_data: dict,
        parameters: dict | None = None,
    ) -> ModelResponse:
        """
        Serve request within an A/B test.

        Randomly routes to model A or B based on configured percentages.

        Args:
            test_id: A/B test ID
            input_data: Input data
            parameters: Optional parameters

        Returns:
            Model response
        """
        config = self._ab_tests.get(test_id)
        if not config:
            raise ValueError(f"A/B test {test_id} not found")

        # Select model based on percentage
        if random.uniform(0, 100) < config.model_a_percentage:
            version_id = config.model_a_id
        else:
            version_id = config.model_b_id

        # Get model and route request
        model = self._registry.get_model(version_id)
        if not model:
            raise ValueError(f"Model {version_id} not found")

        return self._router.serve_request(
            model.model_name,
            input_data,
            version_id=version_id,
            parameters=parameters,
        # TODO: Split this function (40 lines) - KISS principle
        )

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
    # TODO: Split this function (34 lines) - KISS principle
    # SHADOW DEPLOYMENT
    # ======================================================================================

    def start_shadow_deployment(
        self,
        primary_model_id: str,
        shadow_model_id: str,
        traffic_percentage: float = 100.0,
    ) -> str:
        """
        Start shadow deployment for testing new model.

        Args:
            primary_model_id: Production model ID
            shadow_model_id: Shadow model ID (being tested)
            traffic_percentage: % of requests to shadow (0-100)

        Returns:
            Shadow deployment ID
        """
        shadow_id = str(uuid.uuid4())

        deployment = ShadowDeployment(
            shadow_id=shadow_id,
            primary_model_id=primary_model_id,
            shadow_model_id=shadow_model_id,
            traffic_percentage=traffic_percentage,
        )

        with self._lock:
            self._shadow_deployments[shadow_id] = deployment

        _LOG.info(
            f"Started shadow deployment {shadow_id}: "
            f"{shadow_model_id} shadowing {primary_model_id}"
        )

        return shadow_id

    def get_ab_test(self, test_id: str) -> ABTestConfig | None:
        """Get A/B test configuration"""
        return self._ab_tests.get(test_id)

    def get_shadow_deployment(self, shadow_id: str) -> ShadowDeployment | None:
        """Get shadow deployment configuration"""
        return self._shadow_deployments.get(shadow_id)
