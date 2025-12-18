"""Report generation use case - Single Responsibility Principle."""

from collections import Counter
from typing import Any

from .entities import UsageMetric
from .interfaces import MetricsRepository, ReportGenerator


class UsageReportGenerator(ReportGenerator):
    """Usage report generator - SRP: Only generates usage reports."""

    def __init__(self, repository: MetricsRepository):
        self.repository = repository

    def generate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Generate usage report."""
        start_time = data["start_time"]
        end_time = data["end_time"]

        metrics = self.repository.get_range(start_time, end_time)

        return {
            "period": {"start": start_time.isoformat(), "end": end_time.isoformat()},
            "summary": self._calculate_summary(metrics),
            "top_endpoints": self._get_top_endpoints(metrics),
            "hourly_breakdown": self._get_hourly_breakdown(metrics),
        }

    def _calculate_summary(self, metrics: list[UsageMetric]) -> dict[str, Any]:
        """Calculate summary statistics - Complexity < 10."""
        if not metrics:
            return {"total_requests": 0, "unique_users": 0, "avg_response_time": 0}

        total_requests = len([m for m in metrics if m.name == "api_request"])
        unique_users = len(set(m.user_id for m in metrics if m.user_id))
        errors = len([m for m in metrics if m.status_code and m.status_code >= 400])
        error_rate = (errors / total_requests * 100) if total_requests > 0 else 0

        return {
            "total_requests": total_requests,
            "unique_users": unique_users,
            "error_rate": round(error_rate, 2),
            "total_errors": errors,
        }

    def _get_top_endpoints(self, metrics: list[UsageMetric], limit: int = 10) -> list[dict[str, Any]]:
        """Get top endpoints by request count - Complexity < 10."""
        endpoint_counts = Counter(m.endpoint for m in metrics if m.endpoint and m.name == "api_request")

        return [{"endpoint": endpoint, "count": count} for endpoint, count in endpoint_counts.most_common(limit)]

    def _get_hourly_breakdown(self, metrics: list[UsageMetric]) -> list[dict[str, Any]]:
        """Get hourly breakdown - Complexity < 10."""
        hourly_data: dict[str, dict[str, int]] = {}

        for m in metrics:
            if m.name == "api_request":
                hour = m.timestamp.strftime("%Y-%m-%d %H:00")
                if hour not in hourly_data:
                    hourly_data[hour] = {"requests": 0, "errors": 0}

                hourly_data[hour]["requests"] += 1
                if m.status_code and m.status_code >= 400:
                    hourly_data[hour]["errors"] += 1

        return [{"hour": hour, **data} for hour, data in sorted(hourly_data.items())]
