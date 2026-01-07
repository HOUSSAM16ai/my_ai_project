"""سياسات التنبيه الخاصة بأداء المحادثات الإدارية."""

from __future__ import annotations

import logging

from app.services.admin.performance.metrics import PerformanceCategory, PerformanceMetric

logger = logging.getLogger(__name__)


class PerformanceAlertPolicy:
    """مراقب تنبيهات ينبه عند تجاوز حدود الأداء."""

    def __init__(self, latency_threshold_ms: int = 1000) -> None:
        """يضبط الحد الأقصى لزمن الاستجابة المستخدم في التنبيه."""
        self._latency_threshold_ms = latency_threshold_ms

    def check(self, metric: PerformanceMetric) -> None:
        """يفحص المقياس ويطلق تنبيهات عبر السجل عند الحاجة."""
        if metric.latency_ms > self._latency_threshold_ms:
            logger.warning(
                "⚠️ High latency detected: %sms (category: %s, model: %s)",
                metric.latency_ms,
                metric.category,
                metric.model_used,
            )
        if metric.get_category() == PerformanceCategory.SLOW:
            logger.warning(
                "⚠️ Slow request detected: %sms (user: %s, category: %s)",
                metric.latency_ms,
                metric.user_id,
                metric.category,
            )
