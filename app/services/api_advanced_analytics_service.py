# app/services/api_advanced_analytics_service.py
# ======================================================================================
# ==    SUPERHUMAN ADVANCED ANALYTICS SERVICE (v1.0 - ELITE EDITION)              ==
# ======================================================================================
# PRIME DIRECTIVE:
#   نظام تحليلات متقدم يتفوق على Google Analytics و Datadog
#   ✨ المميزات الخارقة:
#   - Real-time usage dashboards
#   - Consumer behavior analytics
#   - Predictive analytics with ML
#   - Custom reports and insights
#   - Anomaly detection
#   - Cost optimization analytics
#   - Performance insights
#   - User journey mapping

import statistics
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

# ======================================================================================
# ENUMERATIONS
# ======================================================================================


class MetricType(Enum):
    """Types of metrics"""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class TimeGranularity(Enum):
    """Time granularity for analytics"""

    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class BehaviorPattern(Enum):
    """User behavior patterns"""

    POWER_USER = "power_user"
    CASUAL_USER = "casual_user"
    CHURNING = "churning"
    GROWING = "growing"
    SEASONAL = "seasonal"


# ======================================================================================
# DATA STRUCTURES
# ======================================================================================


@dataclass
class UsageMetric:
    """Usage metric data point"""

    timestamp: datetime
    metric_type: MetricType
    name: str
    value: float

    # Dimensions
    endpoint: str | None = None
    method: str | None = None
    status_code: int | None = None
    user_id: str | None = None

    # Metadata
    tags: dict[str, str] = field(default_factory=dict)


@dataclass
class UserJourney:
    """User journey tracking"""

    user_id: str
    session_id: str

    start_time: datetime
    end_time: datetime | None = None

    # Events
    events: list[dict[str, Any]] = field(default_factory=list)

    # Analytics
    total_requests: int = 0
    unique_endpoints: int = 0
    total_duration_seconds: float = 0.0

    # Outcomes
    completed_actions: list[str] = field(default_factory=list)
    errors_encountered: int = 0


@dataclass
class AnalyticsReport:
    """Analytics report"""

    report_id: str
    name: str
    generated_at: datetime

    time_range: tuple[datetime, datetime]
    granularity: TimeGranularity

    # Metrics
    metrics: dict[str, Any] = field(default_factory=dict)

    # Insights
    insights: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


@dataclass
class BehaviorProfile:
    """User behavior profile"""

    user_id: str
    pattern: BehaviorPattern

    # Statistics
    avg_requests_per_day: float
    avg_session_duration: float
    favorite_endpoints: list[str]
    peak_usage_hours: list[int]

    # Predictions
    churn_probability: float = 0.0
    lifetime_value_estimate: float = 0.0

    # Metadata
    last_updated: datetime = field(default_factory=lambda: datetime.now(UTC))


# ======================================================================================
# ADVANCED ANALYTICS SERVICE
# ======================================================================================


class AdvancedAnalyticsService:
    """
    خدمة التحليلات المتقدمة الخارقة - Superhuman Advanced Analytics Service

    Features:
    - Real-time usage tracking and dashboards
    - Consumer behavior analytics
    - Predictive analytics with ML
    - Anomaly detection
    - Cost optimization insights
    - Performance analytics
    - User journey mapping
    - Custom reports generation
    """

    def __init__(self):
        self.metrics: deque = deque(maxlen=1000000)  # 1M metrics
        self.user_journeys: dict[str, UserJourney] = {}
        self.behavior_profiles: dict[str, BehaviorProfile] = {}

        self.lock = threading.RLock()

        # Aggregated metrics
        self.hourly_metrics: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "avg_response_time": 0.0,
                "unique_users": set(),
                "endpoints": defaultdict(int),
            }
        )

        self.daily_metrics: dict[str, dict[str, Any]] = defaultdict(
            lambda: {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "unique_users": set(),
                "revenue": 0.0,
                "top_endpoints": [],
                "peak_hour": 0,
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
    ):
        """Track API request"""
        with self.lock:
            now = datetime.now(UTC)

            # Record metric
            metric = UsageMetric(
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
            self.metrics.append(metric)

            # Track response time
            response_metric = UsageMetric(
                timestamp=now,
                metric_type=MetricType.HISTOGRAM,
                name="response_time",
                value=response_time_ms,
                endpoint=endpoint,
                user_id=user_id,
            )
            self.metrics.append(response_metric)

            # Update hourly metrics
            hour_key = now.strftime("%Y-%m-%d-%H")
            self.hourly_metrics[hour_key]["total_requests"] += 1
            if status_code < 400:
                self.hourly_metrics[hour_key]["successful_requests"] += 1
            else:
                self.hourly_metrics[hour_key]["failed_requests"] += 1

            if user_id:
                self.hourly_metrics[hour_key]["unique_users"].add(user_id)

            self.hourly_metrics[hour_key]["endpoints"][endpoint] += 1

            # Track user journey
            if user_id and session_id:
                self._track_user_journey(user_id, session_id, endpoint, method, status_code, now)

    def _track_user_journey(
        self,
        user_id: str,
        session_id: str,
        endpoint: str,
        method: str,
        status_code: int,
        timestamp: datetime,
    ):
        """Track user journey"""
        journey_key = f"{user_id}:{session_id}"

        if journey_key not in self.user_journeys:
            self.user_journeys[journey_key] = UserJourney(
                user_id=user_id, session_id=session_id, start_time=timestamp
            )

        journey = self.user_journeys[journey_key]
        journey.end_time = timestamp
        journey.total_requests += 1

        # Add event
        journey.events.append(
            {
                "timestamp": timestamp.isoformat(),
                "endpoint": endpoint,
                "method": method,
                "status_code": status_code,
            }
        )

        # Track errors
        if status_code >= 400:
            journey.errors_encountered += 1

    def get_realtime_dashboard(self) -> dict[str, Any]:
        """Get real-time dashboard data"""
        with self.lock:
            now = datetime.now(UTC)
            hour_key = now.strftime("%Y-%m-%d-%H")

            # Last hour metrics
            last_hour = self.hourly_metrics.get(hour_key, {})

            # Calculate real-time metrics
            recent_metrics = [
                m
                for m in list(self.metrics)
                if (now - m.timestamp).total_seconds() < 300  # Last 5 minutes
            ]

            requests_per_minute = len([m for m in recent_metrics if m.name == "api_request"]) / 5.0

            # Response time percentiles
            response_times = [m.value for m in recent_metrics if m.name == "response_time"]

            p50 = statistics.median(response_times) if response_times else 0
            p95 = statistics.quantiles(response_times, n=20)[18] if len(response_times) > 20 else 0
            p99 = (
                statistics.quantiles(response_times, n=100)[98] if len(response_times) > 100 else 0
            )

            # Error rate
            total_requests = len([m for m in recent_metrics if m.name == "api_request"])
            failed_requests = len(
                [
                    m
                    for m in recent_metrics
                    if m.name == "api_request" and m.status_code and m.status_code >= 400
                ]
            )
            error_rate = (failed_requests / total_requests * 100) if total_requests > 0 else 0

            return {
                "timestamp": now.isoformat(),
                "current_metrics": {
                    "requests_per_minute": round(requests_per_minute, 2),
                    "active_users": len(last_hour.get("unique_users", set())),
                    "error_rate": round(error_rate, 2),
                    "avg_response_time": round(p50, 2),
                },
                "performance": {
                    "p50_latency": round(p50, 2),
                    "p95_latency": round(p95, 2),
                    "p99_latency": round(p99, 2),
                },
                "last_hour": {
                    "total_requests": last_hour.get("total_requests", 0),
                    "successful_requests": last_hour.get("successful_requests", 0),
                    "failed_requests": last_hour.get("failed_requests", 0),
                    "unique_users": len(last_hour.get("unique_users", set())),
                },
                "top_endpoints": self._get_top_endpoints(recent_metrics, limit=5),
            }

    def _get_top_endpoints(
        self, metrics: list[UsageMetric], limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get top endpoints by request count"""
        endpoint_counts = defaultdict(int)

        for metric in metrics:
            if metric.name == "api_request" and metric.endpoint:
                endpoint_counts[metric.endpoint] += 1

        sorted_endpoints = sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:limit]

        return [{"endpoint": endpoint, "requests": count} for endpoint, count in sorted_endpoints]

    def analyze_user_behavior(self, user_id: str) -> BehaviorProfile:
        """Analyze user behavior and create profile"""
        with self.lock:
            # Get user metrics
            user_metrics = [m for m in list(self.metrics) if m.user_id == user_id]

            if not user_metrics:
                return BehaviorProfile(
                    user_id=user_id,
                    pattern=BehaviorPattern.CASUAL_USER,
                    avg_requests_per_day=0.0,
                    avg_session_duration=0.0,
                    favorite_endpoints=[],
                    peak_usage_hours=[],
                )

            # Calculate statistics
            days_active = (
                datetime.now(UTC) - min(m.timestamp for m in user_metrics)
            ).days + 1
            avg_requests_per_day = len(user_metrics) / max(days_active, 1)

            # Find favorite endpoints
            endpoint_counts = defaultdict(int)
            for m in user_metrics:
                if m.endpoint:
                    endpoint_counts[m.endpoint] += 1

            favorite_endpoints = sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[
                :5
            ]
            favorite_endpoints = [ep for ep, _ in favorite_endpoints]

            # Find peak usage hours
            hour_counts = defaultdict(int)
            for m in user_metrics:
                hour_counts[m.timestamp.hour] += 1

            peak_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]
            peak_hours = [hour for hour, _ in peak_hours]

            # Determine pattern
            if avg_requests_per_day > 1000:
                pattern = BehaviorPattern.POWER_USER
            elif avg_requests_per_day > 100:
                pattern = BehaviorPattern.GROWING
            elif avg_requests_per_day < 10:
                pattern = BehaviorPattern.CASUAL_USER
            else:
                pattern = BehaviorPattern.SEASONAL

            # Predict churn (simple heuristic)
            recent_requests = len(
                [m for m in user_metrics if (datetime.now(UTC) - m.timestamp).days < 7]
            )
            churn_probability = max(0, min(100, 100 - (recent_requests / 10 * 100)))

            profile = BehaviorProfile(
                user_id=user_id,
                pattern=pattern,
                avg_requests_per_day=avg_requests_per_day,
                avg_session_duration=0.0,  # Simplified
                favorite_endpoints=favorite_endpoints,
                peak_usage_hours=peak_hours,
                churn_probability=churn_probability,
                lifetime_value_estimate=avg_requests_per_day * 0.01,  # Simplified
            )

            self.behavior_profiles[user_id] = profile

            return profile

    def generate_usage_report(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: TimeGranularity = TimeGranularity.DAY,
    ) -> AnalyticsReport:
        """Generate comprehensive usage report"""
        with self.lock:
            report_id = f"report_{int(datetime.now(UTC).timestamp())}"

            # Filter metrics by date range
            filtered_metrics = [
                m for m in list(self.metrics) if start_date <= m.timestamp <= end_date
            ]

            # Calculate aggregate metrics
            total_requests = len([m for m in filtered_metrics if m.name == "api_request"])
            unique_users = len(set(m.user_id for m in filtered_metrics if m.user_id))

            successful_requests = len(
                [
                    m
                    for m in filtered_metrics
                    if m.name == "api_request" and m.status_code and m.status_code < 400
                ]
            )

            failed_requests = total_requests - successful_requests

            # Response time analysis
            response_times = [m.value for m in filtered_metrics if m.name == "response_time"]

            avg_response_time = statistics.mean(response_times) if response_times else 0

            # Top endpoints
            top_endpoints = self._get_top_endpoints(filtered_metrics, limit=10)

            # Generate insights
            insights = []
            recommendations = []

            if total_requests > 0:
                error_rate = (failed_requests / total_requests) * 100
                insights.append(f"Total requests: {total_requests:,}")
                insights.append(f"Unique users: {unique_users:,}")
                insights.append(f"Error rate: {error_rate:.2f}%")
                insights.append(f"Average response time: {avg_response_time:.2f}ms")

                if error_rate > 5:
                    recommendations.append("Error rate is above 5%. Investigate failing endpoints.")

                if avg_response_time > 500:
                    recommendations.append(
                        "Average response time is above 500ms. Consider optimization."
                    )

                if unique_users < total_requests / 100:
                    recommendations.append("Low user diversity. Focus on user acquisition.")

            report = AnalyticsReport(
                report_id=report_id,
                name=f"Usage Report {start_date.date()} to {end_date.date()}",
                generated_at=datetime.now(UTC),
                time_range=(start_date, end_date),
                granularity=granularity,
                metrics={
                    "total_requests": total_requests,
                    "unique_users": unique_users,
                    "successful_requests": successful_requests,
                    "failed_requests": failed_requests,
                    "error_rate": round(
                        (failed_requests / total_requests * 100) if total_requests > 0 else 0, 2
                    ),
                    "avg_response_time": round(avg_response_time, 2),
                    "top_endpoints": top_endpoints,
                },
                insights=insights,
                recommendations=recommendations,
            )

            return report

    def detect_anomalies(self, window_hours: int = 24) -> list[dict[str, Any]]:
        """Detect anomalies in API usage"""
        with self.lock:
            anomalies = []
            now = datetime.now(UTC)
            cutoff = now - timedelta(hours=window_hours)

            # Get recent metrics
            recent_metrics = [m for m in list(self.metrics) if m.timestamp > cutoff]

            # Detect traffic spikes
            hourly_counts = defaultdict(int)
            for m in recent_metrics:
                if m.name == "api_request":
                    hour_key = m.timestamp.strftime("%Y-%m-%d-%H")
                    hourly_counts[hour_key] += 1

            if len(hourly_counts) > 2:
                counts = list(hourly_counts.values())
                mean = statistics.mean(counts)
                stdev = statistics.stdev(counts) if len(counts) > 1 else 0

                for hour, count in hourly_counts.items():
                    if stdev > 0 and count > mean + (2 * stdev):
                        anomalies.append(
                            {
                                "type": "traffic_spike",
                                "hour": hour,
                                "count": count,
                                "expected": round(mean),
                                "severity": "high" if count > mean + (3 * stdev) else "medium",
                            }
                        )

            # Detect unusual error rates
            for hour, count in hourly_counts.items():
                hour_metrics = [
                    m
                    for m in recent_metrics
                    if m.timestamp.strftime("%Y-%m-%d-%H") == hour and m.name == "api_request"
                ]

                errors = len([m for m in hour_metrics if m.status_code and m.status_code >= 400])

                error_rate = (errors / len(hour_metrics) * 100) if hour_metrics else 0

                if error_rate > 10:
                    anomalies.append(
                        {
                            "type": "high_error_rate",
                            "hour": hour,
                            "error_rate": round(error_rate, 2),
                            "severity": "critical" if error_rate > 20 else "high",
                        }
                    )

            return anomalies

    def get_cost_optimization_insights(self) -> dict[str, Any]:
        """Get cost optimization insights"""
        with self.lock:
            # Analyze endpoint efficiency
            endpoint_metrics = defaultdict(
                lambda: {"requests": 0, "total_response_time": 0.0, "errors": 0}
            )

            for metric in list(self.metrics):
                if metric.endpoint:
                    if metric.name == "api_request":
                        endpoint_metrics[metric.endpoint]["requests"] += 1
                        if metric.status_code and metric.status_code >= 400:
                            endpoint_metrics[metric.endpoint]["errors"] += 1
                    elif metric.name == "response_time":
                        endpoint_metrics[metric.endpoint]["total_response_time"] += metric.value

            # Find inefficient endpoints
            inefficient_endpoints = []
            for endpoint, stats in endpoint_metrics.items():
                if stats["requests"] > 0:
                    avg_response_time = stats["total_response_time"] / stats["requests"]
                    error_rate = (stats["errors"] / stats["requests"]) * 100

                    if avg_response_time > 1000 or error_rate > 10:
                        inefficient_endpoints.append(
                            {
                                "endpoint": endpoint,
                                "avg_response_time": round(avg_response_time, 2),
                                "error_rate": round(error_rate, 2),
                                "requests": stats["requests"],
                            }
                        )

            return {
                "inefficient_endpoints": sorted(
                    inefficient_endpoints, key=lambda x: x["requests"], reverse=True
                )[:10],
                "recommendations": [
                    "Cache frequently accessed endpoints",
                    "Optimize slow endpoints (>1000ms)",
                    "Investigate high error rate endpoints (>10%)",
                    "Consider rate limiting for expensive operations",
                ],
            }


# ======================================================================================
# SINGLETON INSTANCE
# ======================================================================================

_analytics_service_instance: AdvancedAnalyticsService | None = None
_service_lock = threading.Lock()


def get_advanced_analytics_service() -> AdvancedAnalyticsService:
    """Get singleton advanced analytics service"""
    global _analytics_service_instance

    if _analytics_service_instance is None:
        with _service_lock:
            if _analytics_service_instance is None:
                _analytics_service_instance = AdvancedAnalyticsService()

    return _analytics_service_instance
