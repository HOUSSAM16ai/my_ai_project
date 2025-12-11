"""Session management use case."""

import hashlib
import time
from datetime import UTC, datetime

from app.analytics.domain import SessionStorePort, UserSession, UserStorePort


class SessionManager:
    """Handles session management logic"""

    def __init__(self, session_store: SessionStorePort, user_store: UserStorePort):
        self.session_store = session_store
        self.user_store = user_store

    def start_session(self, user_id: int, device_type: str = "web", entry_page: str = "/") -> str:
        """Start a new user session"""
        session_id = self._generate_session_id(user_id)

        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            start_time=datetime.now(UTC),
            end_time=None,
            duration_seconds=0.0,
            page_views=0,
            events=0,
            conversions=0,
            device_type=device_type,
            entry_page=entry_page,
            exit_page=None,
        )

        self.session_store.add_session(session)

        # Update user session count
        user = self.user_store.get_user(user_id)
        if user:
            user.total_sessions += 1
            self.user_store.update_user(user)

        return session_id

    def end_session(self, session_id: str) -> None:
        """End a user session"""
        session = self.session_store.get_session(session_id)
        if session:
            session.end_time = datetime.now(UTC)
            session.duration_seconds = (session.end_time - session.start_time).total_seconds()
            self.session_store.update_session(session)

    def _generate_session_id(self, user_id: int) -> str:
        """Generate unique session ID"""
        return hashlib.sha256(f"{user_id}{time.time_ns()}".encode()).hexdigest()[:16]
