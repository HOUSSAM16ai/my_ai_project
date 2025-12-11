"""User Analytics Service Facade - Backward Compatible Interface."""

from datetime import datetime
from typing import Any

from app.analytics.application import (
    ABTestManager,
    EventTracker,
    MetricsCalculator,
    NPSManager,
    SessionManager,
    UserSegmentation,
)
from app.analytics.domain import (
    ABTestResults,
    ConversionMetrics,
    EngagementMetrics,
    EventType,
    NPSMetrics,
    RetentionMetrics,
    UserSegment,
)
from app.analytics.infrastructure import (
    InMemoryABTestStore,
    InMemoryActiveUsersStore,
    InMemoryEventStore,
    InMemoryNPSStore,
    InMemorySessionStore,
    InMemoryUserStore,
)


class UserAnalyticsMetricsService:
    """
    User Analytics & Business Metrics Service Facade
    
    Provides backward-compatible interface while delegating to specialized services.
    """

    def __init__(self):
        # Infrastructure
        self.event_store = InMemoryEventStore()
        self.session_store = InMemorySessionStore()
        self.user_store = InMemoryUserStore()
        self.active_users_store = InMemoryActiveUsersStore()
        self.ab_test_store = InMemoryABTestStore()
        self.nps_store = InMemoryNPSStore()

        # Application services
        self.event_tracker = EventTracker(
            self.event_store, self.session_store, self.user_store, self.active_users_store
        )
        self.session_manager = SessionManager(self.session_store, self.user_store)
        self.metrics_calculator = MetricsCalculator(
            self.event_store, self.session_store, self.user_store, self.active_users_store
        )
        self.ab_test_manager = ABTestManager(self.ab_test_store)
        self.nps_manager = NPSManager(self.nps_store)
        self.user_segmentation = UserSegmentation(self.user_store)

    def track_event(
        self,
        user_id: int,
        event_type: EventType,
        event_name: str,
        session_id: str | None = None,
        properties: dict[str, Any] | None = None,
        page_url: str | None = None,
        device_type: str | None = None,
    ) -> str:
        """Track a user event"""
        return self.event_tracker.track_event(
            user_id, event_type, event_name, session_id, properties, page_url, device_type
        )

    def start_session(self, user_id: int, device_type: str = "web", entry_page: str = "/") -> str:
        """Start a new user session"""
        return self.session_manager.start_session(user_id, device_type, entry_page)

    def end_session(self, session_id: str) -> None:
        """End a user session"""
        self.session_manager.end_session(session_id)

    def get_engagement_metrics(self, time_window: str = "30d") -> EngagementMetrics:
        """Get user engagement metrics"""
        return self.metrics_calculator.get_engagement_metrics(time_window)

    def get_conversion_metrics(self, conversion_event: str = "conversion") -> ConversionMetrics:
        """Get conversion metrics"""
        return self.metrics_calculator.get_conversion_metrics(conversion_event)

    def get_retention_metrics(self, cohort_date: datetime | None = None) -> RetentionMetrics:
        """Get user retention metrics"""
        return self.metrics_calculator.get_retention_metrics(cohort_date)

    def record_nps_response(self, user_id: int, score: int, comment: str = "") -> None:
        """Record NPS response"""
        self.nps_manager.record_nps_response(user_id, score, comment)

    def get_nps_metrics(self) -> NPSMetrics:
        """Calculate NPS metrics"""
        return self.nps_manager.get_nps_metrics()

    def create_ab_test(
        self,
        test_name: str,
        variants: list[str],
        traffic_split: dict[str, float] | None = None,
    ) -> str:
        """Create a new A/B test"""
        return self.ab_test_manager.create_ab_test(test_name, variants, traffic_split)

    def assign_variant(self, test_id: str, user_id: int) -> str:
        """Assign user to A/B test variant"""
        return self.ab_test_manager.assign_variant(test_id, user_id)

    def record_ab_conversion(self, test_id: str, user_id: int) -> None:
        """Record conversion for A/B test"""
        self.ab_test_manager.record_ab_conversion(test_id, user_id)

    def get_ab_test_results(self, test_id: str) -> ABTestResults | None:
        """Get A/B test results"""
        return self.ab_test_manager.get_ab_test_results(test_id)

    def segment_users(self) -> dict[UserSegment, list[int]]:
        """Segment users based on behavior"""
        return self.user_segmentation.segment_users()

    def export_metrics_summary(self) -> dict[str, Any]:
        """Export comprehensive analytics summary"""
        engagement = self.get_engagement_metrics()
        conversion = self.get_conversion_metrics()
        retention = self.get_retention_metrics()
        nps = self.get_nps_metrics()
        segments = self.segment_users()

        return {
            "timestamp": datetime.now().isoformat(),
            "engagement": {
                "dau": engagement.dau,
                "wau": engagement.wau,
                "mau": engagement.mau,
                "avg_session_duration": engagement.avg_session_duration,
                "bounce_rate": engagement.bounce_rate,
                "return_rate": engagement.return_rate,
            },
            "conversion": {
                "conversion_rate": conversion.conversion_rate,
                "total_conversions": conversion.total_conversions,
                "avg_time_to_convert": conversion.avg_time_to_convert,
            },
            "retention": {
                "day_1": retention.day_1_retention,
                "day_7": retention.day_7_retention,
                "day_30": retention.day_30_retention,
                "churn_rate": retention.churn_rate,
            },
            "nps": {
                "score": nps.nps_score,
                "promoters": nps.promoters_percent,
                "detractors": nps.detractors_percent,
            },
            "segmentation": {segment.value: len(users) for segment, users in segments.items()},
            "total_users": len(self.user_store.get_all_users()),
            "total_sessions": len(self.session_store.get_recent_sessions(days=365)),
            "total_events": len(self.event_store.get_recent_events(days=365)),
        }
