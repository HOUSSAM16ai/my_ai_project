"""Analytics Facade - Unified interface following Facade Pattern."""

from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

from .ab_test_manager import ABTestManager

# Import components
from .anomaly_detection import StatisticalAnomalyDetector
from .behavior_analysis import UserBehaviorAnalyzer
from .entities import (
    Anomaly,
    BehaviorProfile,
    UsageMetric,
)
from .enums import ABTestVariant, EventType, UserSegment

# Import Application Logic Managers
from .event_tracker import EventTracker
from .in_memory_repository import InMemoryMetricsRepository
from .in_memory_stores import (
    InMemoryABTestStore,
    InMemoryActiveUsersStore,
    InMemoryCohortStore,
    InMemoryEventStore,
    InMemoryNPSStore,
    InMemoryRevenueStore,
    InMemorySessionStore,
    InMemoryUserStore,
)
from .interfaces import AnomalyDetector, MetricsRepository, ReportGenerator
from .metrics_calculator import MetricsCalculator

# Real Models
from .models import (
    ABTestResults,
    CohortAnalysis,
    ConversionMetrics,
    EngagementMetrics,
    NPSMetrics,
    RetentionMetrics,
    RevenueMetrics,
    UserData,
    UserEvent,
    UserSession,
)
from .nps_manager import NPSManager
from .report_generation import UsageReportGenerator
from .session_manager import SessionManager
from .user_segmentation import UserSegmentation
from .value_objects import BehaviorPattern, MetricType


class SystemAnalyticsService:
    """
    System/API Analytics Service.
    Handles system-level metrics (latency, errors, anomalies).
    """

    def __init__(
        self,
        repository: MetricsRepository,
        anomaly_detector: AnomalyDetector,
        report_generator: ReportGenerator,
    ):
        self.repository = repository
        self.anomaly_detector = anomaly_detector
        self.report_generator = report_generator

    def track_request(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        user_id: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> None:
        """Track an API request."""
        metric = UsageMetric(
            timestamp=datetime.now(UTC),
            metric_type=MetricType.COUNTER,
            name="api_request",
            value=1.0,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            user_id=user_id,
            tags=tags or {},
        )
        self.repository.save(metric)

    def get_anomalies(self, window_hours: int = 24) -> list[Anomaly]:
        """Get detected anomalies in the specified time window."""
        metrics = self.repository.get_recent(window_hours)
        return self.anomaly_detector.detect(metrics)

    def generate_report(self, start_time: datetime, end_time: datetime) -> dict[str, Any]:
        """Generate usage report for the specified time range."""
        return self.report_generator.generate({"start_time": start_time, "end_time": end_time})

    def get_realtime_dashboard(self) -> dict[str, Any]:
        """Get real-time dashboard data."""
        recent_metrics = self.repository.get_recent(hours=1)

        total_requests = len([m for m in recent_metrics if m.name == "api_request"])
        errors = len([m for m in recent_metrics if m.status_code and m.status_code >= 400])
        error_rate = (errors / total_requests * 100) if total_requests > 0 else 0

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "last_hour": {
                "total_requests": total_requests,
                "error_rate": round(error_rate, 2),
                "total_errors": errors,
            },
        }


class UserAnalyticsMetricsService:
    """
    User/Business Analytics Service.
    Handles user behavior, sessions, A/B testing, and NPS.

    This is the main facade for the analytics module.
    """

    def __init__(
        self,
        event_tracker: Optional[EventTracker] = None,
        session_manager: Optional[SessionManager] = None,
        ab_test_manager: Optional[ABTestManager] = None,
        nps_manager: Optional[NPSManager] = None,
        segmentation_service: Optional[UserSegmentation] = None,
        metrics_calculator: Optional[MetricsCalculator] = None,
        system_analytics: Optional[SystemAnalyticsService] = None,
        behavior_analyzer: Optional[UserBehaviorAnalyzer] = None,
    ):
        # Initialize defaults if not provided (Backward Compatibility)
        if event_tracker is None:
            # Recreate dependencies manually if calling default constructor
            event_store = InMemoryEventStore()
            session_store = InMemorySessionStore()
            user_store = InMemoryUserStore()
            active_users_store = InMemoryActiveUsersStore()

            event_tracker = EventTracker(event_store, session_store, user_store, active_users_store)
            session_manager = SessionManager(session_store, user_store)

            ab_test_store = InMemoryABTestStore()
            ab_test_manager = ABTestManager(ab_test_store)

            nps_store = InMemoryNPSStore()
            nps_manager = NPSManager(nps_store)

            segmentation_service = UserSegmentation(user_store)

            metrics_calculator = MetricsCalculator(event_store, session_store, user_store, active_users_store)

            metrics_repo = InMemoryMetricsRepository()
            anomaly_detector = StatisticalAnomalyDetector()
            report_generator = UsageReportGenerator(metrics_repo)
            system_analytics = SystemAnalyticsService(metrics_repo, anomaly_detector, report_generator)

            behavior_analyzer = UserBehaviorAnalyzer(metrics_repo)

        self.event_tracker = event_tracker
        self.session_manager = session_manager
        self.ab_test_manager = ab_test_manager
        self.nps_manager = nps_manager
        self.segmentation_service = segmentation_service
        self.metrics_calculator = metrics_calculator
        self.system_analytics = system_analytics
        self.behavior_analyzer = behavior_analyzer

    # --- Event Tracking ---
    def track_event(
        self,
        user_id: int,
        event_type: EventType,
        event_name: str,
        session_id: str | None = None,
        properties: dict[str, Any] | None = None,
    ) -> str:
        """Track a user event."""
        return self.event_tracker.track_event(
            user_id=user_id,
            event_type=event_type,
            event_name=event_name,
            session_id=session_id,
            properties=properties
        )

    def track_request(self, *args, **kwargs):
        """Delegate system request tracking to system analytics."""
        return self.system_analytics.track_request(*args, **kwargs)

    # --- Session Management ---
    def start_session(self, user_id: int, device_type: str = "unknown") -> str:
        return self.session_manager.start_session(user_id, device_type)

    def end_session(self, session_id: str) -> None:
        self.session_manager.end_session(session_id)

    # --- A/B Testing ---
    def create_ab_test(self, test_name: str, variants: List[str], traffic_allocations: List[float] | None = None) -> str:
        """Create A/B test."""
        return self.ab_test_manager.create_ab_test(test_name, variants, traffic_allocations)

    def assign_variant(self, test_id: str, user_id: int) -> str:
        """Assign user to A/B test variant."""
        return self.ab_test_manager.assign_variant(test_id, user_id)

    def get_user_variant(self, test_name: str, user_id: int) -> str:
        """Legacy alias for assign_variant."""
        return self.assign_variant(test_name, user_id)

    def record_ab_conversion(self, test_id: str, user_id: int) -> None:
        """Record a conversion for an A/B test."""
        self.ab_test_manager.record_ab_conversion(test_id, user_id)

    def get_ab_test_results(self, test_id: str) -> ABTestResults:
        """Get results for an A/B test."""
        return self.ab_test_manager.get_ab_test_results(test_id)

    # --- NPS ---
    def submit_nps(self, user_id: int, score: int, feedback: str | None = None) -> None:
        """Submit NPS score."""
        self.nps_manager.record_nps_response(user_id, score, feedback or "")

    def record_nps_response(self, user_id: int, score: int, feedback: str | None = None) -> None:
        """Alias for submit_nps for backward compatibility."""
        self.submit_nps(user_id, score, feedback)

    def get_nps_metrics(self) -> NPSMetrics:
        """Get NPS metrics."""
        return self.nps_manager.get_nps_metrics()

    # --- Metrics & Reporting ---
    def get_engagement_metrics(self, time_window: str = "30d") -> EngagementMetrics:
        """Get user engagement metrics."""
        return self.metrics_calculator.get_engagement_metrics(time_window)

    def get_conversion_metrics(self, conversion_event: str = "conversion") -> ConversionMetrics:
        """Get conversion metrics."""
        return self.metrics_calculator.get_conversion_metrics(conversion_event)

    def get_retention_metrics(self, cohort_date: datetime | None = None) -> RetentionMetrics:
        """Get retention metrics."""
        return self.metrics_calculator.get_retention_metrics(cohort_date)

    def export_metrics_summary(self) -> Dict[str, Any]:
        """Export comprehensive metrics summary."""
        engagement = self.get_engagement_metrics()
        conversion = self.get_conversion_metrics()
        retention = self.get_retention_metrics()
        nps = self.get_nps_metrics()

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "engagement": {
                "dau": engagement.dau,
                "wau": engagement.wau,
                "mau": engagement.mau,
                "bounce_rate": engagement.bounce_rate,
            },
            "conversion": {
                "rate": conversion.conversion_rate,
                "total": conversion.total_conversions,
            },
            "retention": {
                "day_1": retention.day_1_retention,
                "day_7": retention.day_7_retention,
                "day_30": retention.day_30_retention,
                "churn_rate": retention.churn_rate,
            },
            "nps": {
                "score": nps.nps_score,
                "responses": nps.total_responses,
            },
            "segments": self.segment_users(),
        }

    def analyze_user(self, user_id: int) -> BehaviorProfile:
        """Analyze user behavior."""
        return self.behavior_analyzer.analyze(str(user_id))

    def segment_users(self) -> Dict[UserSegment, list[int]]:
        """Segment all users."""
        return self.segmentation_service.segment_users()

    # --- System Analytics Facade Methods ---

    def get_anomalies(self, window_hours: int = 24) -> list[Anomaly]:
        """Get detected anomalies (Delegated to SystemAnalytics)."""
        return self.system_analytics.get_anomalies(window_hours)

    def get_realtime_dashboard(self) -> dict[str, Any]:
        return self.system_analytics.get_realtime_dashboard()

    def generate_report(self, start_time: datetime, end_time: datetime) -> dict[str, Any]:
        return self.system_analytics.generate_report(start_time, end_time)


# --- Factory Functions ---

# Singleton instance
_analytics_service_instance: UserAnalyticsMetricsService | None = None

def get_user_analytics_service() -> UserAnalyticsMetricsService:
    """Factory to create the full UserAnalyticsMetricsService with all dependencies."""
    global _analytics_service_instance
    if _analytics_service_instance is None:
        _analytics_service_instance = UserAnalyticsMetricsService()
    return _analytics_service_instance

def get_analytics_facade() -> UserAnalyticsMetricsService:
    """Factory for legacy compatibility. Returning the main service is safest."""
    return get_user_analytics_service()

# Aliases
AnalyticsFacade = UserAnalyticsMetricsService
get_analytics_service = get_user_analytics_service
reset_analytics_service = lambda: None

def get_instance() -> UserAnalyticsMetricsService:
    global _analytics_service_instance
    if _analytics_service_instance is None:
        _analytics_service_instance = get_user_analytics_service()
    return _analytics_service_instance
