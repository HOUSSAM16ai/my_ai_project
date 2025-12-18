"""Custom report generators - Demonstrates Open/Closed Principle.

These can be added WITHOUT modifying existing code.
"""

from typing import Any

from .entities import UsageMetric
from .interfaces import MetricsRepository, ReportGenerator


class SecurityReportGenerator(ReportGenerator):
    """
    Security-focused report generator - OCP in action.

    Can be added without modifying:
    - ReportGenerator interface
    - UsageReportGenerator
    - Any other existing code
    """

    def __init__(self, repository: MetricsRepository):
        self.repository = repository

    def generate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate security-focused report."""
        start_time = data["start_time"]
        end_time = data["end_time"]

        metrics = self.repository.get_range(start_time, end_time)

        return {
            "period": {"start": start_time.isoformat(), "end": end_time.isoformat()},
            "security_summary": self._analyze_security(metrics),
            "suspicious_patterns": self._detect_suspicious_patterns(metrics),
            "authentication_failures": self._count_auth_failures(metrics),
        }

    def _analyze_security(self, metrics: list[UsageMetric]) -> dict[str, Any]:
        """Analyze security metrics."""
        total = len(metrics)
        errors_4xx = len([m for m in metrics if m.status_code and 400 <= m.status_code < 500])
        errors_5xx = len([m for m in metrics if m.status_code and m.status_code >= 500])

        return {
            "total_requests": total,
            "client_errors_4xx": errors_4xx,
            "server_errors_5xx": errors_5xx,
            "error_rate": round((errors_4xx + errors_5xx) / total * 100, 2) if total > 0 else 0,
        }

    def _detect_suspicious_patterns(self, metrics: list[UsageMetric]) -> list[dict[str, Any]]:
        """Detect suspicious patterns."""
        patterns = []

        user_request_counts = {}
        for m in metrics:
            if m.user_id:
                user_request_counts[m.user_id] = user_request_counts.get(m.user_id, 0) + 1

        for user_id, count in user_request_counts.items():
            if count > 1000:
                patterns.append({"type": "high_request_rate", "user_id": user_id, "count": count})

        return patterns

    def _count_auth_failures(self, metrics: list[UsageMetric]) -> int:
        """Count authentication failures."""
        return len([m for m in metrics if m.status_code == 401 or m.status_code == 403])


class PerformanceReportGenerator(ReportGenerator):
    """Performance-focused report generator - Another OCP example."""

    def __init__(self, repository: MetricsRepository):
        self.repository = repository

    def generate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate performance report."""
        start_time = data["start_time"]
        end_time = data["end_time"]

        metrics = self.repository.get_range(start_time, end_time)

        return {
            "period": {"start": start_time.isoformat(), "end": end_time.isoformat()},
            "performance_summary": self._analyze_performance(metrics),
            "slow_endpoints": self._identify_slow_endpoints(metrics),
        }

    def _analyze_performance(self, metrics: list[UsageMetric]) -> dict[str, Any]:
        """Analyze performance metrics."""
        response_times = [m.value for m in metrics if m.name == "response_time"]

        if not response_times:
            return {"avg_response_time": 0, "max_response_time": 0}

        return {
            "avg_response_time": round(sum(response_times) / len(response_times), 2),
            "max_response_time": max(response_times),
            "min_response_time": min(response_times),
        }

    def _identify_slow_endpoints(self, metrics: list[UsageMetric]) -> list[dict[str, Any]]:
        """Identify slow endpoints."""
        endpoint_times: dict[str, list[float]] = {}

        for m in metrics:
            if m.endpoint and m.name == "response_time":
                if m.endpoint not in endpoint_times:
                    endpoint_times[m.endpoint] = []
                endpoint_times[m.endpoint].append(m.value)

        slow_endpoints = []
        for endpoint, times in endpoint_times.items():
            avg_time = sum(times) / len(times)
            if avg_time > 1000:
                slow_endpoints.append({"endpoint": endpoint, "avg_response_time": round(avg_time, 2)})

        return sorted(slow_endpoints, key=lambda x: x["avg_response_time"], reverse=True)
