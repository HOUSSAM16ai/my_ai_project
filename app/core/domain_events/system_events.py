"""أحداث النطاق النظامي والأمن والواجهات."""

from dataclasses import dataclass
from typing import Any

from app.core.domain_events.base import (
    BoundedContext,
    DomainEvent,
    DomainEventRegistry,
    EventCategory,
)


@DomainEventRegistry.register
@dataclass
class SecurityThreatDetected(DomainEvent):
    def __init__(self, threat_type: str, severity: str, source_ip: str, details: dict[str, Any]):
        super().__init__(
            event_type="SecurityThreatDetected",
            bounded_context=BoundedContext.SECURITY_COMPLIANCE,
            category=EventCategory.SYSTEM,
            payload={
                "threat_type": threat_type,
                "severity": severity,
                "source_ip": source_ip,
                "details": details,
            },
        )


@DomainEventRegistry.register
@dataclass
class AccessDenied(DomainEvent):
    def __init__(self, user_id: str, resource: str, reason: str):
        super().__init__(
            event_type="AccessDenied",
            bounded_context=BoundedContext.SECURITY_COMPLIANCE,
            category=EventCategory.SYSTEM,
            aggregate_id=user_id,
            aggregate_type="User",
            payload={"resource": resource, "reason": reason}
        )


@DomainEventRegistry.register
@dataclass
class ApiRequestReceived(DomainEvent):
    def __init__(self, request_id: str, method: str, endpoint: str):
        super().__init__(
            event_type="ApiRequestReceived",
            bounded_context=BoundedContext.API_GATEWAY,
            category=EventCategory.SYSTEM,
            aggregate_id=request_id,
            aggregate_type="Request",
            payload={"method": method, "endpoint": endpoint},
        )


@DomainEventRegistry.register
@dataclass
class ApiResponseSent(DomainEvent):
    def __init__(self, request_id: str, status_code: int, duration_ms: float):
        super().__init__(
            event_type="ApiResponseSent",
            bounded_context=BoundedContext.API_GATEWAY,
            category=EventCategory.SYSTEM,
            aggregate_id=request_id,
            aggregate_type="Request",
            payload={"status_code": status_code, "duration_ms": duration_ms}
        )


@DomainEventRegistry.register
@dataclass
class RateLimitExceeded(DomainEvent):
    def __init__(self, client_id: str, endpoint: str, limit: int):
        super().__init__(
            event_type="RateLimitExceeded",
            bounded_context=BoundedContext.API_GATEWAY,
            category=EventCategory.SYSTEM,
            aggregate_id=client_id,
            aggregate_type="Client",
            payload={"endpoint": endpoint, "limit": limit}
        )


@DomainEventRegistry.register
@dataclass
class ChatIntentDetected(DomainEvent):
    def __init__(self, conversation_id: str, user_id: str, intent: str, confidence: float, original_message: str):
        super().__init__(
            event_type="ChatIntentDetected",
            bounded_context=BoundedContext.ADMIN_OPERATIONS,
            category=EventCategory.USER,
            aggregate_id=conversation_id,
            aggregate_type="Conversation",
            payload={"user_id": user_id, "intent": intent, "confidence": confidence, "message": original_message}
        )


@DomainEventRegistry.register
@dataclass
class NotificationRequested(DomainEvent):
    def __init__(self, channel: str, recipient: str, subject: str, body: str):
        super().__init__(
            event_type="NotificationRequested",
            bounded_context=BoundedContext.NOTIFICATION_DELIVERY,
            category=EventCategory.INTEGRATION,
            payload={"channel": channel, "recipient": recipient, "subject": subject, "body": body}
        )


@DomainEventRegistry.register
@dataclass
class DataExportRequested(DomainEvent):
    def __init__(self, export_id: str, format: str, filters: dict[str, Any]):
        super().__init__(
            event_type="DataExportRequested",
            bounded_context=BoundedContext.ANALYTICS_REPORTING,
            category=EventCategory.INTEGRATION,
            aggregate_id=export_id,
            aggregate_type="Export",
            payload={"format": format, "filters": filters}
        )
