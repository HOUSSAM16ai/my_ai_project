# app/services/analytics/application/session_manager.py
"""
Session Manager Service
=======================
Single Responsibility: Manage user sessions lifecycle.
"""

from __future__ import annotations

import hashlib
import time
from datetime import datetime
from typing import Protocol

from app.services.analytics.domain.models import EventType, UserSession


class SessionRepository(Protocol):
    """Protocol for session storage"""
    def save(self, session: UserSession) -> None: ...
    def get(self, session_id: str) -> UserSession | None: ...
    def get_by_user(self, user_id: int) -> list[UserSession]: ...
    def update(self, session: UserSession) -> None: ...


class SessionManager:
    """
    Session lifecycle manager.
    
    Responsibilities:
    - Start sessions
    - End sessions
    - Update session activity
    """
    
    def __init__(self, session_repository: SessionRepository):
        self._session_repo = session_repository
    
    def start_session(
        self,
        user_id: int,
        device_type: str = "web",
        entry_page: str = "/",
    ) -> str:
        """Start new user session"""
        session_id = self._generate_session_id(user_id)
        
        session = UserSession(
            session_id=session_id,
            user_id=user_id,
            start_time=datetime.utcnow(),
            device_type=device_type,
            entry_page=entry_page,
        )
        
        self._session_repo.save(session)
        return session_id
    
    def end_session(self, session_id: str) -> None:
        """End user session"""
        session = self._session_repo.get(session_id)
        if session and not session.end_time:
            session.end_time = datetime.utcnow()
            session.duration_seconds = (session.end_time - session.start_time).total_seconds()
            self._session_repo.update(session)
    
    def update_session_activity(
        self,
        session_id: str,
        event_type: EventType,
        page_url: str | None = None,
    ) -> None:
        """Update session with new activity"""
        session = self._session_repo.get(session_id)
        if session:
            session.update_activity(event_type, page_url)
            self._session_repo.update(session)
    
    def get_session(self, session_id: str) -> UserSession | None:
        """Get session by ID"""
        return self._session_repo.get(session_id)
    
    def get_user_sessions(self, user_id: int) -> list[UserSession]:
        """Get all sessions for user"""
        return self._session_repo.get_by_user(user_id)
    
    def _generate_session_id(self, user_id: int) -> str:
        """Generate unique session ID"""
        return hashlib.sha256(
            f"{user_id}{time.time_ns()}".encode()
        ).hexdigest()[:16]
