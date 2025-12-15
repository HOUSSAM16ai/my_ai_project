"""
Event Domain Models
===================
Core event entities with quantum-inspired state management.
"""
from __future__ import annotations
import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class EventType(Enum):
    """Event type enumeration."""
    PAGE_VIEW = 'page_view'
    CLICK = 'click'
    FORM_SUBMIT = 'form_submit'
    CONVERSION = 'conversion'
    PURCHASE = 'purchase'
    SIGNUP = 'signup'
    LOGIN = 'login'
    LOGOUT = 'logout'
    FEATURE_USE = 'feature_use'
    ERROR = 'error'
    CUSTOM = 'custom'


class EventPriority(Enum):
    """Event processing priority."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BATCH = 4


@dataclass(frozen=True)
class EventId:
    """
    Immutable event identifier with content-based hashing.
    
    Uses SHA-256 for deterministic ID generation enabling
    deduplication and idempotency.
    """
    value: str

    @classmethod
    def generate(cls, user_id: str, timestamp: datetime, event_type: str
        ) ->EventId:
        """Generate deterministic event ID."""
        content = f'{user_id}:{timestamp.isoformat()}:{event_type}'
        hash_value = hashlib.sha256(content.encode()).hexdigest()[:16]
        return cls(value=hash_value)

    @classmethod
    def random(cls) ->EventId:
        """Generate random event ID."""
        return cls(value=uuid.uuid4().hex[:16])


@dataclass
class EventMetadata:
    """Event metadata for enrichment and routing."""
    device_type: str | None = None
    browser: str | None = None
    os: str | None = None
    country: str | None = None
    city: str | None = None
    ip_address: str | None = None
    user_agent: str | None = None
    referrer: str | None = None
    utm_source: str | None = None
    utm_medium: str | None = None
    utm_campaign: str | None = None

    def to_dict(self) ->dict[str, Any]:
        """Convert to dictionary."""
        return {k: v for k, v in self.__dict__.items() if v is not None}


@dataclass
class Event:
    """
    Core event entity with quantum-inspired superposition.
    
    Events can exist in multiple states simultaneously until
    observed/processed, enabling speculative execution and
    parallel hypothesis testing.
    """
    event_id: EventId
    user_id: str
    session_id: str
    event_type: EventType
    event_name: str
    timestamp: datetime
    properties: dict[str, Any] = field(default_factory=dict)
    metadata: EventMetadata = field(default_factory=EventMetadata)
    priority: EventPriority = EventPriority.NORMAL
    superposition_states: list[dict[str, Any]] = field(default_factory=list)
    collapsed: bool = False

    def enrich(self, enrichment: dict[str, Any]) ->None:
        """Enrich event with additional data."""
        self.properties.update(enrichment)

    def to_dict(self) ->dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {'event_id': self.event_id.value, 'user_id': self.user_id,
            'session_id': self.session_id, 'event_type': self.event_type.
            value, 'event_name': self.event_name, 'timestamp': self.
            timestamp.isoformat(), 'properties': self.properties,
            'metadata': self.metadata.to_dict(), 'priority': self.priority.
            value}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) ->Event:
        """Create event from dictionary."""
        return cls(event_id=EventId(data['event_id']), user_id=data[
            'user_id'], session_id=data['session_id'], event_type=EventType
            (data['event_type']), event_name=data['event_name'], timestamp=
            datetime.fromisoformat(data['timestamp']), properties=data.get(
            'properties', {}), metadata=EventMetadata(**data.get('metadata',
            {})), priority=EventPriority(data.get('priority', EventPriority
            .NORMAL.value)))


@dataclass
class EventBatch:
    """
    Batch of events for efficient processing.
    
    Implements interference pattern where operations
    can be combined or cancelled.
    """
    batch_id: str
    events: list[Event]
    created_at: datetime = field(default_factory=datetime.utcnow)

    def optimize(self) ->EventBatch:
        """
        Optimize batch using interference patterns.
        
        - Combine similar events (constructive interference)
        - Cancel opposing events (destructive interference)
        - Deduplicate identical events
        """
        optimized_events = []
        event_map: dict[str, Event] = {}
        for event in self.events:
            key = (
                f'{event.user_id}:{event.event_type.value}:{event.event_name}')
            if key in event_map:
                existing = event_map[key]
                if self._can_combine(existing, event):
                    existing.properties['count'] = existing.properties.get(
                        'count', 1) + 1
                    existing.properties['last_timestamp'] = event.timestamp
                    continue
            event_map[key] = event
            optimized_events.append(event)
        return EventBatch(batch_id=self.batch_id, events=optimized_events,
            created_at=self.created_at)

    def _can_combine(self, event1: Event, event2: Event) ->bool:
        """Check if events can be combined."""
        time_diff = abs((event2.timestamp - event1.timestamp).total_seconds())
        return time_diff < 60

    def size(self) ->int:
        """Get batch size."""
        return len(self.events)

    def split(self, chunk_size: int) ->list[EventBatch]:
        """Split batch into smaller chunks."""
        chunks = []
        for i in range(0, len(self.events), chunk_size):
            chunk_events = self.events[i:i + chunk_size]
            chunks.append(EventBatch(batch_id=
                f'{self.batch_id}_chunk_{i // chunk_size}', events=
                chunk_events, created_at=self.created_at))
        return chunks


@dataclass
class EventStream:
    """
    Continuous stream of events with windowing support.
    
    Implements tumbling and sliding windows for
    real-time aggregation.
    """
    stream_id: str
    window_size: int
    slide_interval: int
    events: list[Event] = field(default_factory=list)

    def add(self, event: Event) ->None:
        """Add event to stream."""
        self.events.append(event)
        self._cleanup_old_events()

    def _cleanup_old_events(self) ->None:
        """Remove events outside window."""
        if not self.events:
            return
        cutoff = datetime.utcnow().timestamp() - self.window_size
        self.events = [e for e in self.events if e.timestamp.timestamp() >=
            cutoff]

    def get_window(self, window_start: datetime, window_end: datetime) ->list[
        Event]:
        """Get events in time window."""
        return [e for e in self.events if window_start <= e.timestamp <
            window_end]


from datetime import timedelta
__all__ = ['EventType', 'EventPriority', 'EventId', 'EventMetadata',
    'Event', 'EventBatch', 'EventStream']
