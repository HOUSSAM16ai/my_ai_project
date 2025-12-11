"""User segmentation use case."""

from datetime import UTC, datetime

from app.analytics.domain import UserSegment, UserStorePort


class UserSegmentation:
    """Handles user segmentation logic"""

    def __init__(self, user_store: UserStorePort):
        self.user_store = user_store

    def segment_users(self) -> dict[UserSegment, list[int]]:
        """Segment users based on behavior"""
        now = datetime.now(UTC)
        segments: dict[UserSegment, list[int]] = {segment: [] for segment in UserSegment}

        users = self.user_store.get_all_users()

        for user_id, data in users.items():
            days_since_last_seen = (now - data.last_seen).days
            days_since_first_seen = (now - data.first_seen).days
            total_events = data.total_events

            if days_since_first_seen <= 7:
                segments[UserSegment.NEW].append(user_id)
            elif days_since_last_seen > 30:
                if days_since_last_seen > 90:
                    segments[UserSegment.CHURNED].append(user_id)
                else:
                    segments[UserSegment.AT_RISK].append(user_id)
            elif total_events > 100:
                segments[UserSegment.POWER].append(user_id)
            else:
                segments[UserSegment.ACTIVE].append(user_id)

        return segments
