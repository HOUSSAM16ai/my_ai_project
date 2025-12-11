# app/services/analytics/application/event_tracker.py
"""
Event Tracker Service
=====================
Application service for tracking user events.

Handles event creation, validation, and storage.
"""

from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime
from typing import Any

from app.services.analytics.domain.models import EventType, UserEvent
from app.services.analytics.domain.ports import EventRepositoryPort, SessionRepositoryPort

_LOG = logging.getLogger(__name__)


# ======================================================================================
# EVENT TRACKER SERVICE
# ======================================================================================


class EventTracker:
    """
    Event tracking service.
    
    Responsibilities:
    - Create and validate user events
    - Store events via repository
    - Generate unique event IDs
    - Update session state
    """

    def __init__(
        self,
        event_repository: EventRepositoryPort,
        session_repository: SessionRepositoryPort,
    ):
        """
        Initialize event tracker.
        
        Args:
            event_repository: Event storage repository
            session_repository: Session storage repository
        """
        self._event_repo = event_repository
        self._session_repo = session_repository

    def track_event(
        self,
        user_id: int,
        event_type: EventType,
        event_name: str,
        session_id: str | None = None,
        properties: dict[str, Any] | None = None,
        page_url: str | None = None,
        device_type: str | None = None,
        timestamp: datetime | None = None,
    ) -> str:
        """
        Track a user event.
        
        Args:
            user_id: User identifier
            event_type: Type of event
            event_name: Event name
            session_id: Session identifier (auto-generated if None)
            properties: Additional event properties
            page_url: Page URL where event occurred
            device_type: Device type (mobile, desktop, tablet)
            timestamp: Event timestamp (current time if None)
            
        Returns:
            Generated event ID
        """
        # Generate event ID
        event_id = self._generate_event_id(user_id, event_name)
        
        # Use current time if not provided
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        # Create event
        event = UserEvent(
            event_id=event_id,
            user_id=user_id,
            session_id=session_id or self._generate_session_id(user_id),
            event_type=event_type,
            event_name=event_name,
            timestamp=timestamp,
            properties=properties or {},
            page_url=page_url,
            device_type=device_type,
        )
        
        # Store event
        self._event_repo.store_event(event)
        
        # Update session
        self._update_session(event)
        
        _LOG.debug(f"Tracked event: {event_id} for user {user_id}")
        
        return event_id

    def track_page_view(
        self,
        user_id: int,
        page_url: str,
        session_id: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Track a page view event.
        
        Args:
            user_id: User identifier
            page_url: Page URL
            session_id: Session identifier
            **kwargs: Additional properties
            
        Returns:
            Event ID
        """
        return self.track_event(
            user_id=user_id,
            event_type=EventType.PAGE_VIEW,
            event_name="page_view",
            session_id=session_id,
            page_url=page_url,
            properties=kwargs,
        )

    def track_conversion(
        self,
        user_id: int,
        conversion_name: str,
        session_id: str | None = None,
        value: float | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Track a conversion event.
        
        Args:
            user_id: User identifier
            conversion_name: Name of conversion
            session_id: Session identifier
            value: Conversion value
            **kwargs: Additional properties
            
        Returns:
            Event ID
        """
        properties = kwargs.copy()
        if value is not None:
            properties["value"] = value
        
        return self.track_event(
            user_id=user_id,
            event_type=EventType.CONVERSION,
            event_name=conversion_name,
            session_id=session_id,
            properties=properties,
        )

    def track_purchase(
        self,
        user_id: int,
        amount: float,
        currency: str = "USD",
        session_id: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Track a purchase event.
        
        Args:
            user_id: User identifier
            amount: Purchase amount
            currency: Currency code
            session_id: Session identifier
            **kwargs: Additional properties (product_id, quantity, etc.)
            
        Returns:
            Event ID
        """
        properties = kwargs.copy()
        properties.update({
            "amount": amount,
            "currency": currency,
        })
        
        return self.track_event(
            user_id=user_id,
            event_type=EventType.PURCHASE,
            event_name="purchase",
            session_id=session_id,
            properties=properties,
        )

    def get_user_events(
        self,
        user_id: int,
        event_type: EventType | None = None,
        limit: int = 100,
    ) -> list[UserEvent]:
        """
        Get events for a user.
        
        Args:
            user_id: User identifier
            event_type: Optional event type filter
            limit: Maximum number of events
            
        Returns:
            List of user events
        """
        return self._event_repo.get_events(
            user_id=user_id,
            event_type=event_type,
            limit=limit,
        )

    def _generate_event_id(self, user_id: int, event_name: str) -> str:
        """Generate unique event ID."""
        unique_str = f"{user_id}{event_name}{time.time_ns()}"
        return hashlib.sha256(unique_str.encode()).hexdigest()[:16]

    def _generate_session_id(self, user_id: int) -> str:
        """Generate unique session ID."""
        unique_str = f"session_{user_id}_{time.time_ns()}"
        return hashlib.sha256(unique_str.encode()).hexdigest()[:16]

    def _update_session(self, event: UserEvent) -> None:
        """Update session with new event."""
        # Get or create session
        session = self._session_repo.get_session(event.session_id)
        
        if session is None:
            # Create new session
            from app.services.analytics.domain.models import UserSession
            
            session = UserSession(
                session_id=event.session_id,
                user_id=event.user_id,
                start_time=event.timestamp,
                device_type=event.device_type or "unknown",
                entry_page=event.page_url or "/",
            )
        
        # Update session with event
        session.update_activity(
            event_type=event.event_type,
            page_url=event.page_url,
            timestamp=event.timestamp,
        )
        
        # Store updated session
        self._session_repo.store_session(session)


# ======================================================================================
# EXPORTS
# ======================================================================================

__all__ = ["EventTracker"]
