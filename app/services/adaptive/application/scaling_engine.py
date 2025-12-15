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
        حساب العدد الأمثل من المثيلات باستخدام multi-objective optimization
        """
        _predicted_load, confidence = self.predict_load(service_name,
            current_metrics)
        cpu_util = current_metrics.cpu_usage
        mem_util = current_metrics.memory_usage
        avg_util = (cpu_util + mem_util) / 2
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
        if current_metrics.latency_p99 > 1000:
            scaling_factor = max(scaling_factor, 1.5)
            direction = ScalingDirection.UP
            reason += (
                f' + High latency: P99={current_metrics.latency_p99:.0f}ms')
        if current_metrics.error_rate > 5:
            scaling_factor = max(scaling_factor, 1.3)
            direction = ScalingDirection.UP
            reason += f' + High error rate: {current_metrics.error_rate:.1f}%'
        target_instances = int(current_instances * scaling_factor)
        target_instances = max(1, min(target_instances, 20))
        predicted_impact = {'cpu_reduction': avg_util / target_instances if
            target_instances > 0 else avg_util, 'latency_improvement': 1.0 /
            scaling_factor if scaling_factor > 1 else 1.0, 'cost_increase':
            target_instances / current_instances if current_instances > 0 else
            1.0}
        return ScalingDecision(service_name=service_name, direction=
            direction, current_instances=current_instances,
            target_instances=target_instances, confidence=confidence,
            reason=reason, predicted_impact=predicted_impact, timestamp=
            datetime.now())
