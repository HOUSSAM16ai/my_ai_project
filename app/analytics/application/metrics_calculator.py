"""Metrics calculation use case."""

import statistics
from collections import defaultdict
from datetime import UTC, datetime

from app.analytics.domain import (
    ActiveUsersStorePort,
    ConversionMetrics,
    EngagementMetrics,
    EventStorePort,
    RetentionMetrics,
    SessionStorePort,
    UserStorePort,
)


class MetricsCalculator:
    """Calculates various analytics metrics"""

    def __init__(
        self,
        event_store: EventStorePort,
        session_store: SessionStorePort,
        user_store: UserStorePort,
        active_users_store: ActiveUsersStorePort,
    ):
        self.event_store = event_store
        self.session_store = session_store
        self.user_store = user_store
        self.active_users_store = active_users_store

    def get_engagement_metrics(self, time_window: str = "30d") -> EngagementMetrics:
        """Get user engagement metrics"""
        datetime.now(UTC)

        # Active users
        dau = len(self.active_users_store.get_active_users("1d"))
        wau = len(self.active_users_store.get_active_users("7d"))
        mau = len(self.active_users_store.get_active_users("30d"))

        # Session metrics
        recent_sessions = self.session_store.get_recent_sessions(days=30)
        recent_sessions = [s for s in recent_sessions if s.end_time is not None]

        if recent_sessions:
            avg_session_duration = statistics.mean(s.duration_seconds for s in recent_sessions)

            # Sessions per user
            user_sessions: dict[int, int] = defaultdict(int)
            for session in recent_sessions:
                user_sessions[session.user_id] += 1
            avg_sessions_per_user = statistics.mean(user_sessions.values())

            # Events per session
            avg_events_per_session = statistics.mean(s.events for s in recent_sessions)

            # Bounce rate
            bounced_sessions = sum(1 for s in recent_sessions if s.events <= 1)
            bounce_rate = bounced_sessions / len(recent_sessions)

            # Return rate
            return_users = sum(1 for count in user_sessions.values() if count > 1)
            return_rate = return_users / len(user_sessions) if user_sessions else 0.0
        else:
            avg_session_duration = 0.0
            avg_sessions_per_user = 0.0
            avg_events_per_session = 0.0
            bounce_rate = 0.0
            return_rate = 0.0

        return EngagementMetrics(
            dau=dau,
            wau=wau,
            mau=mau,
            avg_session_duration=avg_session_duration,
            avg_sessions_per_user=avg_sessions_per_user,
            avg_events_per_session=avg_events_per_session,
            bounce_rate=bounce_rate,
            return_rate=return_rate,
            time_window=time_window,
        )

    def get_conversion_metrics(self, conversion_event: str = "conversion") -> ConversionMetrics:
        """Get conversion metrics"""
        datetime.now(UTC)
        recent_events = self.event_store.get_recent_events(days=30)

        # Count conversions
        conversions = [e for e in recent_events if e.event_name == conversion_event]
        unique_visitors = len({e.user_id for e in recent_events})
        unique_converters = len({e.user_id for e in conversions})

        conversion_rate = unique_converters / unique_visitors if unique_visitors > 0 else 0.0

        # Average time to convert
        user_first_event = {}
        user_conversion_time = {}

        for event in sorted(recent_events, key=lambda e: e.timestamp):
            if event.user_id not in user_first_event:
                user_first_event[event.user_id] = event.timestamp
            if event.event_name == conversion_event and event.user_id not in user_conversion_time:
                user_conversion_time[event.user_id] = event.timestamp

        conversion_times = []
        for user_id, conversion_time in user_conversion_time.items():
            if user_id in user_first_event:
                time_diff = (conversion_time - user_first_event[user_id]).total_seconds()
                conversion_times.append(time_diff)

        avg_time_to_convert = statistics.mean(conversion_times) if conversion_times else 0.0

        # Conversion value
        conversion_value = sum(e.properties.get("value", 0.0) for e in conversions)

        return ConversionMetrics(
            conversion_rate=conversion_rate,
            total_conversions=len(conversions),
            total_visitors=unique_visitors,
            avg_time_to_convert=avg_time_to_convert,
            conversion_value=conversion_value,
            funnel_completion_rate=conversion_rate,
            drop_off_points={},
        )

    def get_retention_metrics(self, cohort_date: datetime | None = None) -> RetentionMetrics:
        """Get user retention metrics"""
        from datetime import timedelta

        if cohort_date is None:
            cohort_date = datetime.now(UTC) - timedelta(days=30)

        users = self.user_store.get_all_users()

        # Get cohort users
        cohort_users = [
            user_id for user_id, data in users.items() if data.first_seen.date() == cohort_date.date()
        ]

        cohort_size = len(cohort_users)

        if cohort_size == 0:
            return RetentionMetrics(
                day_1_retention=0.0,
                day_7_retention=0.0,
                day_30_retention=0.0,
                cohort_size=0,
                churn_rate=0.0,
                avg_lifetime_days=0.0,
            )

        # Calculate retention
        now = datetime.now(UTC)
        day_1_active = sum(1 for uid in cohort_users if (now - users[uid].last_seen).days <= 1)
        day_7_active = sum(1 for uid in cohort_users if (now - users[uid].last_seen).days <= 7)
        day_30_active = sum(1 for uid in cohort_users if (now - users[uid].last_seen).days <= 30)

        day_1_retention = day_1_active / cohort_size
        day_7_retention = day_7_active / cohort_size
        day_30_retention = day_30_active / cohort_size

        churn_rate = 1.0 - day_30_retention

        # Average lifetime
        lifetimes = [(users[uid].last_seen - users[uid].first_seen).days for uid in cohort_users]
        avg_lifetime_days = statistics.mean(lifetimes) if lifetimes else 0.0

        return RetentionMetrics(
            day_1_retention=day_1_retention,
            day_7_retention=day_7_retention,
            day_30_retention=day_30_retention,
            cohort_size=cohort_size,
            churn_rate=churn_rate,
            avg_lifetime_days=avg_lifetime_days,
        )
