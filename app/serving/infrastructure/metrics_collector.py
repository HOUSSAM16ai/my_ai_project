"""
Metrics Collector
=================
Collects and manages performance metrics for model serving.
"""

from __future__ import annotations

import random
import threading
import time
from collections import defaultdict, deque
from typing import Any

from app.serving.domain.entities import ModelMetrics, ModelResponse, ModelVersion


class MetricsCollector:
    """
    Metrics Collector - جامع المقاييس
    
    Responsibilities:
    - Collect performance metrics for each model
    - Monitor model health
    - Calculate costs
    - Provide metrics summaries
    """

    def __init__(self):
        self._metrics: dict[str, deque[ModelMetrics]] = defaultdict(lambda: deque(maxlen=10000))
        self._lock = threading.RLock()
        self._monitoring_active = False

    def start_performance_monitoring(self):
        """بدء مراقبة الأداء المستمرة"""
        if self._monitoring_active:
            return

        self._monitoring_active = True

        def monitor():
            while self._monitoring_active:
                try:
                    self.collect_all_metrics()
                    time.sleep(60)  # كل دقيقة
                except Exception as e:
                    print(f"Performance monitoring error: {e}")

        threading.Thread(target=monitor, daemon=True).start()

    def stop_performance_monitoring(self):
        """إيقاف مراقبة الأداء"""
        self._monitoring_active = False

    def collect_all_metrics(self):
        """جمع مقاييس جميع النماذج"""
        with self._lock:
            # في النظام الحقيقي، يتم جمع من نظام المراقبة
            pass

    def update_metrics(self, version_id: str, response: ModelResponse):
        """
        تحديث مقاييس النموذج
        
        Args:
            version_id: معرف النسخة
            response: استجابة النموذج
        """
        # في النظام الحقيقي، يتم تحديث قاعدة بيانات المقاييس
        # هنا نحن فقط نتتبع في الذاكرة
        with self._lock:
            # يمكن توسيع هذا لتسجيل المقاييس الفعلية
            pass

    def calculate_cost(self, model: ModelVersion, output: Any) -> float:
        """
        حساب تكلفة الطلب
        
        Args:
            model: نسخة النموذج
            output: نتيجة النموذج
            
        Returns:
            التكلفة بالدولار
        """
        # في النظام الحقيقي، يتم حساب حسب عدد الرموز ونوع النموذج
        # هنا محاكاة بسيطة
        return random.uniform(0.001, 0.01)

    def get_model_metrics_summary(self, version_id: str) -> dict[str, Any]:
        """
        الحصول على ملخص مقاييس النموذج
        
        Args:
            version_id: معرف النسخة
            
        Returns:
            ملخص المقاييس
        """
        metrics_list = list(self._metrics.get(version_id, []))

        if not metrics_list:
            return {
                "total_requests": 0,
                "avg_latency": 0,
                "total_cost": 0,
            }

        total_requests = sum(m.total_requests for m in metrics_list)
        avg_latency = sum(m.avg_latency_ms for m in metrics_list) / len(metrics_list)
        total_cost = sum(m.cost_usd for m in metrics_list)

        return {
            "total_requests": total_requests,
            "avg_latency": avg_latency,
            "total_cost": total_cost,
        }

    def get_all_metrics(self, version_id: str) -> list[ModelMetrics]:
        """
        الحصول على جميع مقاييس النموذج
        
        Args:
            version_id: معرف النسخة
            
        Returns:
            قائمة المقاييس
        """
        with self._lock:
            return list(self._metrics.get(version_id, []))
