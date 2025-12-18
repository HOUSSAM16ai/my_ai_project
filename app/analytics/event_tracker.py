"""Event tracking use case."""

import hashlib
import time
from datetime import UTC, datetime
from typing import Any

from . import (
    ActiveUsersStorePort,
    EventStorePort,
    EventType,
    SessionStorePort,
    UserData,
    UserEvent,
    UserSegment,
    UserSession,
    UserStorePort,
)


class EventTracker:
    """Handles event tracking logic"""

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
        if session_id is None:
            session_id = self._generate_session_id(user_id)

        event_id = self._generate_event_id(user_id, event_name)

        event = UserEvent(
            event_id=event_id,
            user_id=user_id,
            session_id=session_id,
            event_type=event_type,
            event_name=event_name,
            timestamp=datetime.now(UTC),
            properties=properties or {},
            page_url=page_url,
            device_type=device_type,
        )

        self.event_store.add_event(event)

        # Update active users
        self.active_users_store.add_active_user(user_id, "1d")
        self.active_users_store.add_active_user(user_id, "7d")
        self.active_users_store.add_active_user(user_id, "30d")

        # Update session
        self._update_session(session_id, user_id, event_type, page_url, device_type)

        # Update user data
        self._update_user(user_id, event_type)

        return event_id

    def _generate_event_id(self, user_id: int, event_name: str) -> str:
        """Generate unique event ID"""
        return hashlib.sha256(f"{user_id}{event_name}{time.time_ns()}".encode()).hexdigest()[:16]

    def _generate_session_id(self, user_id: int) -> str:
        """Generate unique session ID"""
        return hashlib.sha256(f"{user_id}{time.time_ns()}".encode()).hexdigest()[:16]

    def _update_session(
        self,
        session_id: str,
        user_id: int,
        event_type: EventType,
        page_url: str | None,
        device_type: str | None,
    ) -> None:
        """Update session with new event"""
        session = self.session_store.get_session(session_id)

        if session:
            session.events += 1
            if event_type == EventType.PAGE_VIEW:
                session.page_views += 1
            if event_type == EventType.CONVERSION:
                session.conversions += 1
            session.end_time = datetime.now(UTC)
            session.duration_seconds = (session.end_time - session.start_time).total_seconds()
            session.exit_page = page_url or session.exit_page
            self.session_store.update_session(session)
        else:
            # Create new session
            new_session = UserSession(
                session_id=session_id,
                user_id=user_id,
                start_time=datetime.now(UTC),
                end_time=None,
                duration_seconds=0.0,
                page_views=1 if event_type == EventType.PAGE_VIEW else 0,
                events=1,
                conversions=1 if event_type == EventType.CONVERSION else 0,
                device_type=device_type or "unknown",
                entry_page=page_url or "/",
                exit_page=None,
            )
            self.session_store.add_session(new_session)

    def _update_user(self, user_id: int, event_type: EventType) -> None:
        """Update user data with new event"""
        user = self.user_store.get_user(user_id)

        if user:
            user.last_seen = datetime.now(UTC)
            user.total_events += 1
            if event_type == EventType.CONVERSION:
                user.total_conversions += 1
            self.user_store.update_user(user)
        else:
            # Create new user
            new_user = UserData(
                user_id=user_id,
                first_seen=datetime.now(UTC),
                last_seen=datetime.now(UTC),
                total_events=1,
                total_sessions=0,
                total_conversions=1 if event_type == EventType.CONVERSION else 0,
                segment=UserSegment.NEW,
            )
            self.user_store.add_user(new_user)
