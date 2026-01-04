"""
AI Scaling Engine
=================
محرك التوسع الذكي المدعوم بالذكاء الاصطناعي.
يستخدم ML للتنبؤ بالحمل واتخاذ قرارات التوسع.
"""
from __future__ import annotations

import statistics
from collections import defaultdict
from datetime import datetime

from app.services.adaptive.domain.models import ScalingDecision, ScalingDirection, ServiceMetrics

class AIScalingEngine:
    """
    محرك التوسع الذكي المدعوم بالذكاء الاصطناعي
    يستخدم ML للتنبؤ بالحمل واتخاذ قرارات التوسع
    """

    def __init__(self):
        self.historical_patterns = defaultdict(list)
        self.scaling_history = []
        self.learning_rate = 0.1

    def predict_load(self, service_name: str, current_metrics:
        ServiceMetrics, time_window_minutes: int=15) ->tuple[float, float]:
        """
        التنبؤ بالحمل المستقبلي باستخدام time series analysis
        Returns: (predicted_load, confidence)
        """
        history = self.historical_patterns[service_name]
        if len(history) < 10:
            return current_metrics.request_rate, 0.3
        recent_loads = [h.request_rate for h in history[-20:]]
        avg_load = statistics.mean(recent_loads)
        if len(recent_loads) >= 2:
            trend = (recent_loads[-1] - recent_loads[0]) / len(recent_loads)
        else:
            trend = 0
        predicted_load = avg_load + trend * time_window_minutes
        variance = statistics.variance(recent_loads) if len(recent_loads
            ) > 1 else 0
        confidence = max(0.5, min(0.95, 1.0 - variance / (avg_load + 1)))
        return max(0, predicted_load), confidence

    def calculate_optimal_instances(self, service_name: str,
        current_metrics: ServiceMetrics, current_instances: int
        ) ->ScalingDecision:
        """
        حساب العدد الأمثل من المثيلات | Calculate optimal number of instances
        
        يستخدم multi-objective optimization لتحديد العدد الأمثل
        Uses multi-objective optimization to determine optimal number
        """
        _predicted_load, confidence = self.predict_load(service_name,
            current_metrics)
        
        avg_util = self._calculate_average_utilization(current_metrics)
        scaling_factor, direction, reason = self._determine_scaling_direction(
            avg_util, current_instances
        )
        scaling_factor, direction, reason = self._adjust_for_latency(
            current_metrics, scaling_factor, direction, reason
        )
        scaling_factor, direction, reason = self._adjust_for_error_rate(
            current_metrics, scaling_factor, direction, reason
        )
        
        target_instances = self._calculate_target_instances(
            current_instances, scaling_factor
        )
        predicted_impact = self._calculate_predicted_impact(
            avg_util, target_instances, current_instances, scaling_factor
        )
        
        return ScalingDecision(service_name=service_name, direction=
            direction, current_instances=current_instances,
            target_instances=target_instances, confidence=confidence,
            reason=reason, predicted_impact=predicted_impact, timestamp=
            datetime.now())

    def _calculate_average_utilization(self, metrics: ServiceMetrics) -> float:
        """
        حساب متوسط الاستخدام | Calculate average utilization
        
        Args:
            metrics: مقاييس الخدمة | Service metrics
            
        Returns:
            متوسط الاستخدام | Average utilization percentage
        """
        return (metrics.cpu_usage + metrics.memory_usage) / 2

    def _determine_scaling_direction(
        self, avg_util: float, current_instances: int
    ) -> tuple[float, ScalingDirection, str]:
        """
        تحديد اتجاه التوسع | Determine scaling direction
        
        Args:
            avg_util: متوسط الاستخدام | Average utilization
            current_instances: عدد المثيلات الحالي | Current instances
            
        Returns:
            (عامل التوسع، الاتجاه، السبب) | (scaling factor, direction, reason)
        """
        target_util = 65.0
        
        if avg_util > 80:
            scaling_factor = avg_util / target_util
            direction = ScalingDirection.UP
            reason = f'High utilization: {avg_util:.1f}% (threshold: 80%)'
        elif avg_util < 30 and current_instances > 1:
            scaling_factor = avg_util / target_util
            direction = ScalingDirection.DOWN
            reason = f'Low utilization: {avg_util:.1f}% (threshold: 30%)'
        else:
            scaling_factor = 1.0
            direction = ScalingDirection.STABLE
            reason = f'Optimal utilization: {avg_util:.1f}%'
        
        return scaling_factor, direction, reason

    def _adjust_for_latency(
        self,
        metrics: ServiceMetrics,
        scaling_factor: float,
        direction: ScalingDirection,
        reason: str
    ) -> tuple[float, ScalingDirection, str]:
        """
        تعديل التوسع حسب الكمون | Adjust scaling for latency
        
        Args:
            metrics: مقاييس الخدمة | Service metrics
            scaling_factor: عامل التوسع | Scaling factor
            direction: اتجاه التوسع | Scaling direction
            reason: السبب | Reason
            
        Returns:
            (عامل التوسع المحدث، الاتجاه، السبب) | (updated scaling factor, direction, reason)
        """
        if metrics.latency_p99 > 1000:
            scaling_factor = max(scaling_factor, 1.5)
            direction = ScalingDirection.UP
            reason += f' + High latency: P99={metrics.latency_p99:.0f}ms'
        
        return scaling_factor, direction, reason

    def _adjust_for_error_rate(
        self,
        metrics: ServiceMetrics,
        scaling_factor: float,
        direction: ScalingDirection,
        reason: str
    ) -> tuple[float, ScalingDirection, str]:
        """
        تعديل التوسع حسب معدل الخطأ | Adjust scaling for error rate
        
        Args:
            metrics: مقاييس الخدمة | Service metrics
            scaling_factor: عامل التوسع | Scaling factor
            direction: اتجاه التوسع | Scaling direction
            reason: السبب | Reason
            
        Returns:
            (عامل التوسع المحدث، الاتجاه، السبب) | (updated scaling factor, direction, reason)
        """
        if metrics.error_rate > 5:
            scaling_factor = max(scaling_factor, 1.3)
            direction = ScalingDirection.UP
            reason += f' + High error rate: {metrics.error_rate:.1f}%'
        
        return scaling_factor, direction, reason

    def _calculate_target_instances(
        self, current_instances: int, scaling_factor: float
    ) -> int:
        """
        حساب العدد المستهدف من المثيلات | Calculate target instances
        
        Args:
            current_instances: عدد المثيلات الحالي | Current instances
            scaling_factor: عامل التوسع | Scaling factor
            
        Returns:
            العدد المستهدف | Target instances (between 1 and 20)
        """
        target_instances = int(current_instances * scaling_factor)
        return max(1, min(target_instances, 20))

    def _calculate_predicted_impact(
        self,
        avg_util: float,
        target_instances: int,
        current_instances: int,
        scaling_factor: float
    ) -> dict[str, float]:
        """
        حساب التأثير المتوقع | Calculate predicted impact
        
        Args:
            avg_util: متوسط الاستخدام | Average utilization
            target_instances: العدد المستهدف | Target instances
            current_instances: العدد الحالي | Current instances
            scaling_factor: عامل التوسع | Scaling factor
            
        Returns:
            التأثير المتوقع | Predicted impact metrics
        """
        return {
            'cpu_reduction': avg_util / target_instances if target_instances > 0 else avg_util,
            'latency_improvement': 1.0 / scaling_factor if scaling_factor > 1 else 1.0,
            'cost_increase': target_instances / current_instances if current_instances > 0 else 1.0
        }
