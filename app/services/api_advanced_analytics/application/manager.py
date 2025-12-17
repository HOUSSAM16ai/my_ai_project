"""
API Advanced Analytics - Application Manager
============================================
Core service orchestration and use case coordination.

This manager coordinates all analytics operations using domain models
and ports (dependency inversion).
"""

import statistics
import threading
from collections import defaultdict, deque
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import uuid4

from ..domain import (
    AnalyticsReport,
    BehaviorPattern,
    BehaviorProfile,
    BehaviorRepositoryPort,
    JourneyRepositoryPort,
    MetricType,
    MetricsRepositoryPort,
    ReportRepositoryPort,
    TimeGranularity,
    UsageMetric,
    UserJourney,
)


class AnalyticsManager:
    """
    Advanced Analytics Service Manager.

    Coordinates all analytics operations:
    - Real-time usage tracking
    - User behavior analysis
    - Report generation
    - Anomaly detection
    - Cost optimization insights
    """

    def __init__(
        self,
        metrics_repo: MetricsRepositoryPort,
        journey_repo: JourneyRepositoryPort,
        behavior_repo: BehaviorRepositoryPort,
        report_repo: ReportRepositoryPort,
    ):
        """Initialize with repository dependencies."""
        self._metrics_repo = metrics_repo
        self._journey_repo = journey_repo
        self._behavior_repo = behavior_repo
        self._report_repo = report_repo

        # In-memory caches for real-time data
        self._metrics_cache: deque = deque(maxlen=1000000)
        self._lock = threading.RLock()

        # Aggregated metrics
        self._hourly_metrics: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "avg_response_time": 0.0,
                "unique_users": set(),
                "endpoints": defaultdict(int),
            }
        )

    def track_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        user_id: str | None = None,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """
        Track an API request with all its details.

        Args:
            endpoint: API endpoint path
            method: HTTP method (GET, POST, etc.)
            status_code: HTTP status code
            response_time_ms: Response time in milliseconds
            user_id: Optional user identifier
            session_id: Optional session identifier
            metadata: Additional metadata tags
        """
        with self._lock:
            now = datetime.now(UTC)

            # Create and save request metric
            request_metric = UsageMetric(
                timestamp=now,
                metric_type=MetricType.COUNTER,
                name="api_request",
                value=1.0,
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                user_id=user_id,
                tags=metadata or {},
            )
            self._metrics_cache.append(request_metric)
            self._metrics_repo.save_metric(request_metric)

            # Create and save response time metric
            response_metric = UsageMetric(
                timestamp=now,
                metric_type=MetricType.HISTOGRAM,
                name="response_time",
                value=response_time_ms,
                endpoint=endpoint,
                user_id=user_id,
            )
            self._metrics_cache.append(response_metric)
            self._metrics_repo.save_metric(response_metric)

            # Update aggregated metrics
            self._update_hourly_metrics(now, endpoint, status_code, user_id)

            # Track user journey if applicable
            if user_id and session_id:
                self._track_journey_event(user_id, session_id, endpoint, method, status_code, now)

    def _update_hourly_metrics(
        self, timestamp: datetime, endpoint: str, status_code: int, user_id: str | None
    ) -> None:
        """Update hourly aggregated metrics."""
        hour_key = timestamp.strftime("%Y-%m-%d-%H")

        self._hourly_metrics[hour_key]["total_requests"] += 1

        if status_code < 400:
            self._hourly_metrics[hour_key]["successful_requests"] += 1
        else:
            self._hourly_metrics[hour_key]["failed_requests"] += 1

        if user_id:
            self._hourly_metrics[hour_key]["unique_users"].add(user_id)

        self._hourly_metrics[hour_key]["endpoints"][endpoint] += 1

    def _track_journey_event(
        self,
        user_id: str,
        session_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        timestamp: datetime,
    ) -> None:
        """Track an event in a user's journey."""
        # Get or create journey
        journey = self._journey_repo.get_journey(session_id)

        if journey is None:
            journey = UserJourney(
                user_id=user_id,
                session_id=session_id,
                start_time=timestamp,
            )

        # Update journey
        journey.end_time = timestamp
        journey.add_event({
            "timestamp": timestamp.isoformat(),
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
        })

        if status_code >= 400:
            journey.errors_encountered += 1

        # Save updated journey
        self._journey_repo.save_journey(journey)

    def get_realtime_dashboard(self) -> dict[str, Any]:
        """
        Get real-time dashboard with current metrics.

        Returns comprehensive real-time analytics including:
        - Current request rate
        - Active users
        - Error rate
        - Performance percentiles
        - Top endpoints
        """
        with self._lock:
            now = datetime.now(UTC)
            hour_key = now.strftime("%Y-%m-%d-%H")

            # Get current hour metrics
            current_hour = self._hourly_metrics.get(hour_key, {})

            # Get recent metrics (last 5 minutes)
            recent_metrics = [
                m for m in list(self._metrics_cache)
                if (now - m.timestamp).total_seconds() < 300
            ]

            # Calculate request rate
            request_metrics = [m for m in recent_metrics if m.name == "api_request"]
            requests_per_minute = len(request_metrics) / 5.0

            # Calculate response time percentiles
            response_times = [m.value for m in recent_metrics if m.name == "response_time"]

            p50 = statistics.median(response_times) if response_times else 0
            p95 = (
                statistics.quantiles(response_times, n=20)[18]
                if len(response_times) > 20
                else 0
            )
            p99 = (
                statistics.quantiles(response_times, n=100)[98]
                if len(response_times) > 100
                else 0
            )

            # Calculate error rate
            failed_requests = len([
                m for m in request_metrics
                if m.status_code and m.status_code >= 400
            ])
            error_rate = (
                (failed_requests / len(request_metrics) * 100)
                if request_metrics
                else 0
            )

            # Get top endpoints
            top_endpoints = self._get_top_endpoints(recent_metrics, limit=5)

            return {
                "timestamp": now.isoformat(),
                "current_metrics": {
                    "requests_per_minute": round(requests_per_minute, 2),
                    "active_users": len(current_hour.get("unique_users", set())),
                    "error_rate": round(error_rate, 2),
                    "avg_response_time": round(p50, 2),
                },
                "performance": {
                    "p50_latency": round(p50, 2),
                    "p95_latency": round(p95, 2),
                    "p99_latency": round(p99, 2),
                },
                "last_hour": {
                    "total_requests": current_hour.get("total_requests", 0),
                    "successful_requests": current_hour.get("successful_requests", 0),
                    "failed_requests": current_hour.get("failed_requests", 0),
                    "unique_users": len(current_hour.get("unique_users", set())),
                },
                "top_endpoints": top_endpoints,
            }

    def _get_top_endpoints(self, metrics: list[UsageMetric], limit: int = 10) -> list[dict[str, Any]]:
        """Get top endpoints by request count."""
        endpoint_counts: dict[str, int] = defaultdict(int)

        for metric in metrics:
            if metric.name == "api_request" and metric.endpoint:
                endpoint_counts[metric.endpoint] += 1

        # Sort and limit
        sorted_endpoints = sorted(
            endpoint_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:limit]

        return [
            {"endpoint": endpoint, "requests": count}
            for endpoint, count in sorted_endpoints
        ]

    def analyze_user_behavior(self, user_id: str) -> BehaviorProfile:
        """
        Analyze user behavior and create behavior profile.

        Uses machine learning-like heuristics to classify user behavior
        and predict churn probability.

        Args:
            user_id: User identifier

        Returns:
            BehaviorProfile with classification and predictions
        """
        # Get user's journeys
        journeys = self._journey_repo.get_user_journeys(user_id, limit=30)

        if not journeys:
            # No data - create default profile
            return BehaviorProfile(
                user_id=user_id,
                pattern=BehaviorPattern.CASUAL_USER,
                avg_requests_per_day=0.0,
                avg_session_duration=0.0,
                favorite_endpoints=[],
                peak_usage_hours=[],
            )

        # Calculate statistics
        total_requests = sum(j.total_requests for j in journeys)
        avg_requests_per_day = total_requests / max(len(journeys), 1)

        total_duration = sum(j.duration_seconds for j in journeys)
        avg_session_duration = total_duration / max(len(journeys), 1)

        # Find favorite endpoints
        endpoint_counts: dict[str, int] = defaultdict(int)
        for journey in journeys:
            for event in journey.events:
                endpoint = event.get("endpoint")
                if endpoint:
                    endpoint_counts[endpoint] += 1

        favorite_endpoints = sorted(
            endpoint_counts.keys(),
            key=lambda x: endpoint_counts[x],
            reverse=True,
        )[:5]

        # Find peak usage hours
        hour_counts: dict[int, int] = defaultdict(int)
        for journey in journeys:
            hour_counts[journey.start_time.hour] += 1

        peak_usage_hours = sorted(
            hour_counts.keys(),
            key=lambda x: hour_counts[x],
            reverse=True,
        )[:3]

        # Classify behavior pattern
        if avg_requests_per_day > 50:
            pattern = BehaviorPattern.POWER_USER
        elif avg_requests_per_day < 5:
            pattern = BehaviorPattern.CASUAL_USER
        elif len(journeys) >= 7:
            # Check if activity is declining
            recent_requests = sum(j.total_requests for j in journeys[:3])
            older_requests = sum(j.total_requests for j in journeys[-3:])
            if recent_requests < older_requests * 0.5:
                pattern = BehaviorPattern.CHURNING
            elif recent_requests > older_requests * 1.5:
                pattern = BehaviorPattern.GROWING
            else:
                pattern = BehaviorPattern.SEASONAL
        else:
            pattern = BehaviorPattern.CASUAL_USER

        # Calculate churn probability (simple heuristic)
        churn_probability = 0.0
        if pattern == BehaviorPattern.CHURNING:
            churn_probability = 0.8
        elif pattern == BehaviorPattern.CASUAL_USER:
            churn_probability = 0.3
        elif pattern == BehaviorPattern.POWER_USER:
            churn_probability = 0.1

        # Estimate lifetime value (simple heuristic based on activity)
        lifetime_value_estimate = avg_requests_per_day * 365 * 0.1

        profile = BehaviorProfile(
            user_id=user_id,
            pattern=pattern,
            avg_requests_per_day=avg_requests_per_day,
            avg_session_duration=avg_session_duration,
            favorite_endpoints=favorite_endpoints,
            peak_usage_hours=peak_usage_hours,
            churn_probability=churn_probability,
            lifetime_value_estimate=lifetime_value_estimate,
        )

        # Save profile
        self._behavior_repo.save_profile(profile)

        return profile

    def generate_usage_report(
        self,
        name: str,
        start_time: datetime,
        end_time: datetime,
        granularity: TimeGranularity = TimeGranularity.HOUR,
    ) -> AnalyticsReport:
        """
        Generate comprehensive usage report.

        Args:
            name: Report name
            start_time: Start of time range
            end_time: End of time range
            granularity: Time granularity for aggregation

        Returns:
            AnalyticsReport with metrics and insights
        """
        report_id = str(uuid4())
        report = AnalyticsReport(
            report_id=report_id,
            name=name,
            generated_at=datetime.now(UTC),
            time_range=(start_time, end_time),
            granularity=granularity,
        )

        # Get metrics for time range
        metrics = self._metrics_repo.get_metrics(start_time, end_time)

        # Calculate aggregated metrics
        request_metrics = [m for m in metrics if m.name == "api_request"]
        response_metrics = [m for m in metrics if m.name == "response_time"]

        total_requests = len(request_metrics)
        successful_requests = len([m for m in request_metrics if m.status_code and m.status_code < 400])
        failed_requests = total_requests - successful_requests

        report.add_metric("total_requests", total_requests)
        report.add_metric("successful_requests", successful_requests)
        report.add_metric("failed_requests", failed_requests)
        report.add_metric("success_rate", (successful_requests / total_requests * 100) if total_requests > 0 else 0)

        # Response time statistics
        if response_metrics:
            response_times = [m.value for m in response_metrics]
            report.add_metric("avg_response_time", statistics.mean(response_times))
            report.add_metric("median_response_time", statistics.median(response_times))
            report.add_metric("p95_response_time", statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else 0)

        # Generate insights
        if failed_requests / total_requests > 0.05:
            report.add_insight(f"High error rate detected: {failed_requests / total_requests * 100:.1f}%")
            report.add_recommendation("Investigate error patterns and implement fixes")

        if total_requests > 10000:
            report.add_insight(f"High traffic volume: {total_requests:,} requests")
            report.add_recommendation("Consider scaling infrastructure to handle load")

        # Save report
        self._report_repo.save_report(report)

        return report

    def detect_anomalies(self, window_hours: int = 24) -> list[dict[str, Any]]:
        """
        Detect anomalies in request patterns.

        Uses statistical methods to identify unusual patterns.

        Args:
            window_hours: Time window to analyze (in hours)

        Returns:
            List of detected anomalies
        """
        now = datetime.now(UTC)
        start_time = now - timedelta(hours=window_hours)

        # Get metrics for window
        metrics = [
            m for m in self._metrics_cache
            if m.timestamp >= start_time
        ]

        anomalies = []

        # Check for error rate spikes
        request_metrics = [m for m in metrics if m.name == "api_request"]
        if request_metrics:
            error_metrics = [m for m in request_metrics if m.status_code and m.status_code >= 400]
            error_rate = len(error_metrics) / len(request_metrics)

            if error_rate > 0.1:  # > 10% error rate
                anomalies.append({
                    "type": "high_error_rate",
                    "severity": "high",
                    "value": error_rate * 100,
                    "threshold": 10.0,
                    "message": f"Error rate {error_rate * 100:.1f}% exceeds threshold of 10%",
                })

        # Check for response time anomalies
        response_metrics = [m for m in metrics if m.name == "response_time"]
        if len(response_metrics) > 100:
            response_times = [m.value for m in response_metrics]
            mean_response = statistics.mean(response_times)
            stdev_response = statistics.stdev(response_times)

            # Check for values beyond 3 standard deviations
            threshold = mean_response + (3 * stdev_response)
            outliers = [r for r in response_times if r > threshold]

            if len(outliers) > len(response_times) * 0.01:  # > 1% outliers
                anomalies.append({
                    "type": "slow_responses",
                    "severity": "medium",
                    "value": len(outliers),
                    "threshold": threshold,
                    "message": f"{len(outliers)} slow responses detected (> {threshold:.0f}ms)",
                })

        return anomalies

    def get_cost_optimization_insights(self) -> dict[str, Any]:
        """
        Get cost optimization insights based on usage patterns.

        Analyzes usage to identify cost-saving opportunities.

        Returns:
            Dictionary with optimization recommendations
        """
        now = datetime.now(UTC)

        # Analyze last 7 days
        start_time = now - timedelta(days=7)
        recent_metrics = [
            m for m in self._metrics_cache
            if m.timestamp >= start_time
        ]

        insights = {
            "analysis_period": "last_7_days",
            "total_requests": len([m for m in recent_metrics if m.name == "api_request"]),
            "recommendations": [],
        }

        # Identify low-traffic endpoints
        endpoint_counts: dict[str, int] = defaultdict(int)
        for metric in recent_metrics:
            if metric.name == "api_request" and metric.endpoint:
                endpoint_counts[metric.endpoint] += 1

        low_traffic = [
            endpoint for endpoint, count in endpoint_counts.items()
            if count < 100  # Less than 100 requests in 7 days
        ]

        if low_traffic:
            insights["recommendations"].append({
                "type": "low_traffic_endpoints",
                "count": len(low_traffic),
                "message": f"{len(low_traffic)} endpoints with very low traffic",
                "action": "Consider deprecating unused endpoints to reduce maintenance costs",
            })

        # Check for peak/off-peak usage
        hour_counts: dict[int, int] = defaultdict(int)
        for metric in recent_metrics:
            if metric.name == "api_request":
                hour_counts[metric.timestamp.hour] += 1

        if hour_counts:
            peak_hour = max(hour_counts.items(), key=lambda x: x[1])
            off_peak_hour = min(hour_counts.items(), key=lambda x: x[1])

            if peak_hour[1] > off_peak_hour[1] * 5:  # 5x difference
                insights["recommendations"].append({
                    "type": "peak_usage_pattern",
                    "peak_hour": peak_hour[0],
                    "off_peak_hour": off_peak_hour[0],
                    "message": "Significant peak/off-peak usage pattern detected",
                    "action": "Consider auto-scaling or scheduled scaling to optimize costs",
                })

        return insights
