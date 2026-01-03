# app/services/adaptive/application/health_monitor.py
"""
Predictive Health Monitor
==========================
نظام مراقبة صحة تنبؤي يكتشف المشاكل قبل حدوثها.
"""

from __future__ import annotations

import statistics
from collections import defaultdict

from app.services.adaptive.domain.models import ServiceHealth, ServiceMetrics

class PredictiveHealthMonitor:
    """
    نظام مراقبة صحة تنبؤي يكتشف المشاكل قبل حدوثها
    """

    def __init__(self):
        self.health_patterns = defaultdict(list)
        self.anomaly_threshold = 2.5  # Standard deviations

    def analyze_health(
        self, service_name: str, current_metrics: ServiceMetrics
    ) -> tuple[ServiceHealth, list[str]]:
        """
        تحليل صحة الخدمة والتنبؤ بالمشاكل
        Analyze service health and predict issues
        
        Args:
            service_name: اسم الخدمة | Service name
            current_metrics: المقاييس الحالية | Current metrics
            
        Returns:
            حالة الصحة وقائمة التحذيرات | Health status and warnings list
        """
        warnings = []

        # Store and maintain metrics history
        self._store_metrics_history(service_name, current_metrics)

        # Check critical conditions
        critical_warnings = self._check_critical_conditions(current_metrics)
        if critical_warnings:
            return ServiceHealth.CRITICAL, critical_warnings

        # Check degraded conditions
        degraded_warnings = self._check_degraded_conditions(current_metrics)
        
        # Check for anomalies
        anomaly_warnings = self._detect_anomalies(service_name, current_metrics)
        
        # Combine all warnings
        all_warnings = degraded_warnings + anomaly_warnings
        if all_warnings:
            return ServiceHealth.DEGRADED, all_warnings

        return ServiceHealth.HEALTHY, []

    def _store_metrics_history(
        self, service_name: str, current_metrics: ServiceMetrics
    ) -> None:
        """
        تخزين وصيانة تاريخ المقاييس | Store and maintain metrics history
        
        Args:
            service_name: اسم الخدمة | Service name
            current_metrics: المقاييس الحالية | Current metrics
        """
        self.health_patterns[service_name].append(current_metrics)

        # Keep only recent history (last 1000 entries)
        if len(self.health_patterns[service_name]) > 1000:
            self.health_patterns[service_name] = self.health_patterns[service_name][-1000:]

    def _check_critical_conditions(
        self, current_metrics: ServiceMetrics
    ) -> list[str]:
        """
        فحص الظروف الحرجة | Check critical conditions
        
        Args:
            current_metrics: المقاييس الحالية | Current metrics
            
        Returns:
            قائمة التحذيرات الحرجة | Critical warnings list
        """
        warnings = []

        if current_metrics.cpu_usage > 95:
            warnings.append(f"CRITICAL: CPU usage at {current_metrics.cpu_usage:.1f}%")
        if current_metrics.memory_usage > 95:
            warnings.append(f"CRITICAL: Memory usage at {current_metrics.memory_usage:.1f}%")
        if current_metrics.error_rate > 50:
            warnings.append(f"CRITICAL: Error rate at {current_metrics.error_rate:.1f}%")

        return warnings

    def _check_degraded_conditions(
        self, current_metrics: ServiceMetrics
    ) -> list[str]:
        """
        فحص ظروف التدهور | Check degraded conditions
        
        Args:
            current_metrics: المقاييس الحالية | Current metrics
            
        Returns:
            قائمة تحذيرات التدهور | Degraded warnings list
        """
        warnings = []

        if current_metrics.cpu_usage > 85:
            warnings.append(f"WARNING: High CPU usage {current_metrics.cpu_usage:.1f}%")
        if current_metrics.memory_usage > 85:
            warnings.append(f"WARNING: High memory usage {current_metrics.memory_usage:.1f}%")
        if current_metrics.error_rate > 10:
            warnings.append(f"WARNING: Elevated error rate {current_metrics.error_rate:.1f}%")
        if current_metrics.latency_p99 > 2000:
            warnings.append(f"WARNING: High latency P99={current_metrics.latency_p99:.0f}ms")

        return warnings

    def _detect_anomalies(self, service_name: str, current_metrics: ServiceMetrics) -> list[str]:
        """
        كشف الشذوذ باستخدام statistical analysis
        """
        history = self.health_patterns[service_name]

        if len(history) < 30:  # Need sufficient history
            return []

        anomalies = []

        # Check each metric for anomalies
        metrics_to_check = {
            "cpu_usage": [m.cpu_usage for m in history[-30:]],
            "memory_usage": [m.memory_usage for m in history[-30:]],
            "latency_p99": [m.latency_p99 for m in history[-30:]],
            "error_rate": [m.error_rate for m in history[-30:]],
        }

        for metric_name, values in metrics_to_check.items():
            if len(values) < 2:
                continue

            mean = statistics.mean(values)
            stdev = statistics.stdev(values)

            current_value = getattr(current_metrics, metric_name)

            # Check if current value is an anomaly
            if stdev > 0:
                z_score = abs((current_value - mean) / stdev)
                if z_score > self.anomaly_threshold:
                    anomalies.append(
                        f"ANOMALY: {metric_name}={current_value:.1f} "
                        f"(mean={mean:.1f}, z-score={z_score:.1f})"
                    )

        return anomalies

    def predict_failure(
        self, service_name: str, lookahead_minutes: int = 15  # noqa: unused variable
    ) -> tuple[float, list[str]]:
        """
        التنبؤ باحتمالية الفشل في المستقبل القريب
        Returns: (failure_probability, risk_factors)
        """
        history = self.health_patterns[service_name]

        if len(history) < 10:
            return 0.0, []

        risk_factors = []
        risk_score = 0.0

        # Analyze trends
        recent_cpu = [m.cpu_usage for m in history[-10:]]
        recent_mem = [m.memory_usage for m in history[-10:]]
        recent_errors = [m.error_rate for m in history[-10:]]

        # CPU trend
        if len(recent_cpu) >= 2:
            cpu_trend = (recent_cpu[-1] - recent_cpu[0]) / len(recent_cpu)
            if cpu_trend > 5:  # Increasing rapidly
                risk_score += 0.3
                risk_factors.append(f"CPU trending up: +{cpu_trend:.1f}% per interval")

        # Memory trend
        if len(recent_mem) >= 2:
            mem_trend = (recent_mem[-1] - recent_mem[0]) / len(recent_mem)
            if mem_trend > 5:
                risk_score += 0.3
                risk_factors.append(f"Memory trending up: +{mem_trend:.1f}% per interval")

        # Error rate trend
        if len(recent_errors) >= 2:
            error_trend = (recent_errors[-1] - recent_errors[0]) / len(recent_errors)
            if error_trend > 1:
                risk_score += 0.4
                risk_factors.append(f"Errors trending up: +{error_trend:.1f}% per interval")

        failure_probability = min(1.0, risk_score)

        return failure_probability, risk_factors
