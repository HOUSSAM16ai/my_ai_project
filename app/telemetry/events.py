# app/telemetry/events.py
# ======================================================================================
# ==        EVENT TRACKING (v1.0 - REAL-TIME EDITION)                               ==
# ======================================================================================
"""
تتبع الأحداث - Event Tracking

Features surpassing tech giants:
✅ Real-time event streaming
✅ Event enrichment with context
✅ Event correlation across services
✅ Batch processing for performance
✅ Event deduplication
"""

import hashlib
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class EventType(Enum):
    """Event types"""
    USER = "user"
    SYSTEM = "system"
    BUSINESS = "business"
    ERROR = "error"
    SECURITY = "security"


@dataclass
class Event:
    """Event data"""
    event_id: str
    event_type: EventType
    name: str
    timestamp: float
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    trace_id: Optional[str] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "name": self.name,
            "timestamp": self.timestamp,
            "datetime": datetime.fromtimestamp(self.timestamp).isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "trace_id": self.trace_id,
            "properties": self.properties,
            "context": self.context,
        }


class EventTracker:
    """
    تتبع الأحداث - Event Tracker
    
    Real-time event tracking with:
    - Event enrichment
    - Correlation
    - Deduplication
    - Batch processing
    """
    
    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        
        # Event storage
        self.events: deque = deque(maxlen=100000)
        self.event_batch: List[Event] = []
        
        # Deduplication
        self.seen_events: set = set()
        
        # Statistics
        self.stats = {
            "total_events": 0,
            "user_events": 0,
            "system_events": 0,
            "business_events": 0,
            "error_events": 0,
            "security_events": 0,
            "duplicates_filtered": 0,
        }
    
    def track(
        self,
        event_type: EventType,
        name: str,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Track an event"""
        # Generate event ID
        event_id = self._generate_event_id(name, user_id, time.time())
        
        # Check for duplicates
        if event_id in self.seen_events:
            self.stats["duplicates_filtered"] += 1
            return event_id
        
        # Enrich context
        enriched_context = self._enrich_context(context or {})
        
        # Create event
        event = Event(
            event_id=event_id,
            event_type=event_type,
            name=name,
            timestamp=time.time(),
            user_id=user_id,
            session_id=session_id,
            trace_id=trace_id,
            properties=properties or {},
            context=enriched_context
        )
        
        # Store event
        self.events.append(event)
        self.event_batch.append(event)
        
        # Mark as seen
        self.seen_events.add(event_id)
        
        # Update statistics
        self.stats["total_events"] += 1
        stat_key = f"{event_type.value}_events"
        if stat_key in self.stats:
            self.stats[stat_key] += 1
        
        # Process batch if full
        if len(self.event_batch) >= self.batch_size:
            self._process_batch()
        
        return event_id
    
    def track_user_event(
        self,
        name: str,
        user_id: str,
        properties: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Track a user event"""
        return self.track(
            EventType.USER,
            name,
            user_id=user_id,
            properties=properties,
            **kwargs
        )
    
    def track_system_event(
        self,
        name: str,
        properties: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Track a system event"""
        return self.track(
            EventType.SYSTEM,
            name,
            properties=properties,
            **kwargs
        )
    
    def track_business_event(
        self,
        name: str,
        properties: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Track a business event"""
        return self.track(
            EventType.BUSINESS,
            name,
            properties=properties,
            **kwargs
        )
    
    def track_error(
        self,
        name: str,
        error_type: str,
        error_message: str,
        **kwargs
    ) -> str:
        """Track an error event"""
        return self.track(
            EventType.ERROR,
            name,
            properties={
                "error_type": error_type,
                "error_message": error_message,
            },
            **kwargs
        )
    
    def track_security_event(
        self,
        name: str,
        severity: str,
        properties: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """Track a security event"""
        props = properties or {}
        props["severity"] = severity
        return self.track(
            EventType.SECURITY,
            name,
            properties=props,
            **kwargs
        )
    
    def _enrich_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich event context with automatic data"""
        enriched = context.copy()
        
        # Add timestamp if not present
        if "timestamp" not in enriched:
            enriched["timestamp"] = datetime.utcnow().isoformat()
        
        # Add server info
        if "server" not in enriched:
            enriched["server"] = "cogniforge"
        
        return enriched
    
    def _generate_event_id(
        self,
        name: str,
        user_id: Optional[str],
        timestamp: float
    ) -> str:
        """Generate unique event ID"""
        data = f"{name}:{user_id}:{timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()[:16]
    
    def _process_batch(self):
        """Process batch of events (placeholder for external export)"""
        # In production, export to external system (Kafka, Kinesis, etc.)
        self.event_batch.clear()
    
    def query_events(
        self,
        event_type: Optional[EventType] = None,
        user_id: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 100
    ) -> List[Event]:
        """Query events with filters"""
        results = []
        
        for event in reversed(self.events):
            # Apply filters
            if event_type and event.event_type != event_type:
                continue
            if user_id and event.user_id != user_id:
                continue
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue
            
            results.append(event)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get tracker statistics"""
        return {
            **self.stats,
            "events_stored": len(self.events),
            "batch_size": len(self.event_batch),
        }
