"""
A/B Testing Engine
==================
Manages A/B tests between different model versions.
Responsible for test configuration, traffic splitting, and analysis.
"""
from __future__ import annotations

import threading
import time
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from app.services.serving.domain.models import ABTestConfig

if TYPE_CHECKING:
    from app.services.serving.application.model_registry import ModelRegistry

class ABTestEngine:
    """
    A/B Testing Engine - محرك اختبار A/B

    Responsibilities:
    - Create and manage A/B test configurations
    - Route requests based on split percentages
    - Analyze test results and determine winner
    """

    def __init__(self, model_registry: ModelRegistry):
        self._model_registry = model_registry
        self._ab_tests: dict[str, ABTestConfig] = {}
        self._lock = threading.RLock()

    def start_ab_test(self, model_a_id: str, model_b_id: str,
        split_percentage: float=50.0, duration_hours: int=24) ->str:
        """
        بدء اختبار A/B بين نموذجين

        Args:
            model_a_id: معرف النموذج A
            model_b_id: معرف النموذج B
            split_percentage: نسبة الطلبات للنموذج A (الباقي لـ B)
            duration_hours: مدة الاختبار بالساعات

        Returns:
            معرف الاختبار
        """
        test_id = str(uuid.uuid4())
        config = ABTestConfig(test_id=test_id, model_a_id=model_a_id,
            model_b_id=model_b_id, model_a_percentage=split_percentage,
            model_b_percentage=100.0 - split_percentage, duration_hours=
            duration_hours)
        with self._lock:
            self._ab_tests[test_id] = config

        def end_test() -> None:
            time.sleep(duration_hours * 3600)
            self.analyze_ab_test(test_id)
        threading.Thread(target=end_test, daemon=True).start()
        return test_id

    def analyze_ab_test(self, test_id: str, metrics_getter: callable) ->dict[
        str, Any]:
        """
        تحليل نتائج اختبار A/B وتحديد الفائز

        Args:
            test_id: معرف الاختبار
            metrics_getter: دالة للحصول على مقاييس النموذج

        Returns:
            نتائج التحليل
        """
        config = self._ab_tests.get(test_id)
        if not config:
            return {'error': 'Test not found'}
        metrics_a = metrics_getter(config.model_a_id)
        metrics_b = metrics_getter(config.model_b_id)
        if config.success_metric == 'latency':
            winner = 'A' if metrics_a['avg_latency'] < metrics_b['avg_latency'
                ] else 'B'
        elif config.success_metric == 'cost':
            winner = 'A' if metrics_a['total_cost'] < metrics_b['total_cost'
                ] else 'B'
        else:
            winner = 'A'
        with self._lock:
            config.winner = winner
            config.ended_at = datetime.now(UTC)
        return {'test_id': test_id, 'winner': winner, 'model_a_metrics':
            metrics_a, 'model_b_metrics': metrics_b, 'duration': (datetime.
            now(UTC) - config.started_at).total_seconds() / 3600}

    def get_ab_test_status(self, test_id: str) ->(ABTestConfig | None):
        """
        الحصول على حالة اختبار A/B

        Args:
            test_id: معرف الاختبار

        Returns:
            تكوين الاختبار أو None
        """
        with self._lock:
            return self._ab_tests.get(test_id)
