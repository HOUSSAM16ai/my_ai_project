"""Analytics domain ports (interfaces)."""

from datetime import datetime
from typing import Protocol

from .enums import UserSegment
from .models import UserData, UserEvent, UserSession


class EventStorePort(Protocol):
    """Port for event storage"""

    def add_event(self, event: UserEvent) -> None:
        """Store an event"""
        ...

    def get_events(
        self, user_id: int | None = None, start_time: datetime | None = None
    ) -> list[UserEvent]:
        """Retrieve events"""
        ...

    def get_recent_events(self, days: int = 30) -> list[UserEvent]:
        """Get events from last N days"""
        ...


class SessionStorePort(Protocol):
    """Port for session storage"""

    def add_session(self, session: UserSession) -> None:
        """Store a session"""
        ...

    def get_session(self, session_id: str) -> UserSession | None:
        """Retrieve a session"""
        ...

    def update_session(self, session: UserSession) -> None:
        """Update a session"""
        ...

    def get_recent_sessions(self, days: int = 30) -> list[UserSession]:
        """Get sessions from last N days"""
        ...


class UserStorePort(Protocol):
    """Port for user data storage"""

    def add_user(self, user_data: UserData) -> None:
        """Store user data"""
        ...

    def get_user(self, user_id: int) -> UserData | None:
        """Retrieve user data"""
        ...

    def update_user(self, user_data: UserData) -> None:
        """Update user data"""
        ...

    def get_all_users(self) -> dict[int, UserData]:
        """Get all users"""
        ...

    def get_users_by_segment(self, segment: UserSegment) -> list[int]:
        """Get users in a segment"""
        ...


class ActiveUsersStorePort(Protocol):
    """Port for active users tracking"""

    def add_active_user(self, user_id: int, period: str) -> None:
        """Mark user as active for period (1d, 7d, 30d)"""
        ...

    def get_active_users(self, period: str) -> set[int]:
        """Get active users for period"""
        ...

    def clear_period(self, period: str) -> None:
        """Clear active users for period"""
        ...


class ABTestStorePort(Protocol):
    """Port for A/B test storage"""

    def add_test(self, test_id: str, test_data: dict) -> None:
        """Store A/B test"""
        ...

    def get_test(self, test_id: str) -> dict | None:
        """Retrieve A/B test"""
        ...

    def update_test(self, test_id: str, test_data: dict) -> None:
        """Update A/B test"""
        ...

    def get_all_tests(self) -> dict[str, dict]:
        """Get all A/B tests"""
        ...


class NPSStorePort(Protocol):
    """Port for NPS response storage"""

    def add_response(self, response: dict) -> None:
        """Store NPS response"""
        ...

    def get_responses(self, days: int | None = None) -> list[dict]:
        """Get NPS responses"""
        ...
