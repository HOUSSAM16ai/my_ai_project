# app/services/analytics/infrastructure/in_memory_repository.py
"""
In-Memory Repository Implementations
=====================================
Concrete implementations of analytics repository ports.

Uses in-memory data structures for development and testing.
Production systems should use PostgreSQL, ClickHouse, or similar.
"""

from __future__ import annotations

import threading
from collections import defaultdict, deque
from datetime import datetime
from typing import Any

from app.services.analytics.domain.models import EventType, UserEvent, UserSession
from app.services.analytics.domain.ports import EventRepositoryPort, SessionRepositoryPort


# ======================================================================================
# IN-MEMORY EVENT REPOSITORY
# ======================================================================================


class InMemoryEventRepository(EventRepositoryPort):
    """
    In-memory event repository.
    
    Features:
    - Thread-safe operations
    - Bounded deque for memory management
    - Fast filtering and retrieval
    """

    def __init__(self, max_events: int = 100000):
        """
        Initialize event repository.
        
        Args:
            max_events: Maximum number of events to retain
        """
        self._events: deque[UserEvent] = deque(maxlen=max_events)
        self._events_by_user: dict[int, list[UserEvent]] = defaultdict(list)
        self._events_by_session: dict[str, list[UserEvent]] = defaultdict(list)
        self._lock = threading.RLock()

    def store_event(self, event: UserEvent) -> None:
        """Store a user event."""
        with self._lock:
            self._events.append(event)
            self._events_by_user[event.user_id].append(event)
            self._events_by_session[event.session_id].append(event)

    def get_events(
        self,
        user_id: int | None = None,
        session_id: str | None = None,
        event_type: EventType | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 1000,
    ) -> list[UserEvent]:
        """Retrieve events matching filters."""
        with self._lock:
            # Start with appropriate subset
            if user_id is not None:
                candidates = self._events_by_user.get(user_id, [])
            elif session_id is not None:
                candidates = self._events_by_session.get(session_id, [])
            else:
                candidates = list(self._events)
            
            # Apply filters
            results = []
            for event in candidates:
                # Type filter
                if event_type is not None and event.event_type != event_type:
                    continue
                
                # Time filters
                if start_time is not None and event.timestamp < start_time:
                    continue
                if end_time is not None and event.timestamp > end_time:
                    continue
                
                results.append(event)
                
                if len(results) >= limit:
                    break
            
            return results

    def count_events(
        self,
        user_id: int | None = None,
        event_type: EventType | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> int:
        """Count events matching filters."""
        events = self.get_events(
            user_id=user_id,
            event_type=event_type,
            start_time=start_time,
            end_time=end_time,
            limit=float('inf'),  # type: ignore
        )
        return len(events)

    def delete_old_events(self, before: datetime) -> int:
        """Delete events older than specified time."""
        with self._lock:
            # Filter out old events
            new_events = [e for e in self._events if e.timestamp >= before]
            deleted_count = len(self._events) - len(new_events)
            
            # Rebuild indices
            self._events.clear()
            self._events_by_user.clear()
            self._events_by_session.clear()
            
            for event in new_events:
                self._events.append(event)
                self._events_by_user[event.user_id].append(event)
                self._events_by_session[event.session_id].append(event)
            
            return deleted_count


# ======================================================================================
# IN-MEMORY SESSION REPOSITORY
# ======================================================================================


class InMemorySessionRepository(SessionRepositoryPort):
    """
    In-memory session repository.
    
    Features:
    - Thread-safe operations
    - Fast lookups by session ID and user ID
    - Session lifecycle management
    """

    def __init__(self):
        """Initialize session repository."""
        self._sessions: dict[str, UserSession] = {}
        self._sessions_by_user: dict[int, list[str]] = defaultdict(list)
        self._lock = threading.RLock()

    def store_session(self, session: UserSession) -> None:
        """Store or update a user session."""
        with self._lock:
            session_id = session.session_id
            user_id = session.user_id
            
            # Store session
            self._sessions[session_id] = session
            
            # Update user index if new session
            if session_id not in self._sessions_by_user[user_id]:
                self._sessions_by_user[user_id].append(session_id)

    def get_session(self, session_id: str) -> UserSession | None:
        """Retrieve session by ID."""
        with self._lock:
            return self._sessions.get(session_id)

    def get_user_sessions(
        self,
        user_id: int,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> list[UserSession]:
        """Retrieve all sessions for a user."""
        with self._lock:
            session_ids = self._sessions_by_user.get(user_id, [])
            sessions = []
            
            for session_id in session_ids:
                session = self._sessions.get(session_id)
                if session is None:
                    continue
                
                # Time filters
                if start_time is not None and session.start_time < start_time:
                    continue
                if end_time is not None and session.start_time > end_time:
                    continue
                
                sessions.append(session)
            
            return sessions

    def get_active_sessions(self, since: datetime | None = None) -> list[UserSession]:
        """Get all active sessions."""
        with self._lock:
            active = []
            
            for session in self._sessions.values():
                # Consider session active if no end time or recent activity
                if session.end_time is None:
                    if since is None or session.start_time >= since:
                        active.append(session)
                elif since is not None and session.end_time >= since:
                    active.append(session)
            
            return active


# ======================================================================================
# EXPORTS
# ======================================================================================

__all__ = [
    "InMemoryEventRepository",
    "InMemorySessionRepository",
]
