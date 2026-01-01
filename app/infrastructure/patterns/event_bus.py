"""Event Bus pattern for event-driven architecture."""
import logging
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import uuid4

logger = logging.getLogger(__name__)

@dataclass
class Event:
    """Base event class."""
    event_id: str = field(default_factory=lambda : str(uuid4()))
    event_type: str = ''
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda : datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)

class EventBus:
    """Event bus for publish-subscribe pattern."""

    def __init__(self):
        self._subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._async_subscribers: dict[str, list[Callable]] = defaultdict(list)
        self._event_history: list[Event] = []
        self._max_history = 1000

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        """Subscribe to event type."""
        self._subscribers[event_type].append(handler)
        logger.debug(f'Subscribed handler to {event_type}')

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from event type."""
        if handler in self._subscribers[event_type]:
            self._subscribers[event_type].remove(handler)
        if handler in self._async_subscribers[event_type]:
            self._async_subscribers[event_type].remove(handler)

    def publish(self, event: Event) -> None:
        """Publish event to subscribers."""
        self._add_to_history(event)
        for handler in self._subscribers.get(event.event_type, []):
            try:
                handler(event)
            except Exception as e:
                logger.error(f'Error in event handler: {e}')
        for handler in self._subscribers.get('*', []):
            try:
                handler(event)
            except Exception as e:
                logger.error(f'Error in wildcard handler: {e}')

    async def _safe_async_call(self, handler: Callable, event: Event):
        """Safely call async handler."""
        try:
            await handler(event)
        except Exception as e:
            logger.error(f'Error in async event handler: {e}')

    def _add_to_history(self, event: Event):
        """Add event to history."""
        self._event_history.append(event)
        if len(self._event_history) > self._max_history:
            self._event_history = self._event_history[-self._max_history:]

    def get_history(self, event_type: (str | None)=None, limit: int=100
        ) ->list[Event]:
        """Get event history."""
        if event_type:
            events = [e for e in self._event_history if e.event_type ==
                event_type]
        else:
            events = self._event_history
        return events[-limit:]

_global_event_bus = EventBus()

def get_event_bus() ->EventBus:
    """Get global event bus instance."""
    return _global_event_bus
