"""
User Domain Events.

أحداث متعلقة بإدارة المستخدمين (User Management Events).

المبادئ:
- Single Responsibility: فقط أحداث المستخدمين
- Grouped by Context: مجمعة حسب السياق
"""

from dataclasses import dataclass

from app.core.domain_events.base import (
    BoundedContext,
    DomainEvent,
    DomainEventRegistry,
    EventCategory,
)


@DomainEventRegistry.register
@dataclass
class UserCreated(DomainEvent):
    """حدث إنشاء مستخدم جديد."""

    def __init__(self, user_id: str, email: str, name: str):
        super().__init__(
            event_type="UserCreated",
            bounded_context=BoundedContext.USER_MANAGEMENT,
            category=EventCategory.USER,
            aggregate_id=user_id,
            aggregate_type="User",
            payload={"email": email, "name": name},
        )


@DomainEventRegistry.register
@dataclass
class UserUpdated(DomainEvent):
    """حدث تحديث بيانات مستخدم."""

    def __init__(self, user_id: str, changes: dict[str, object]):
        super().__init__(
            event_type="UserUpdated",
            bounded_context=BoundedContext.USER_MANAGEMENT,
            category=EventCategory.USER,
            aggregate_id=user_id,
            aggregate_type="User",
            payload={"changes": changes},
        )


@DomainEventRegistry.register
@dataclass
class UserDeleted(DomainEvent):
    """حدث حذف مستخدم."""

    def __init__(self, user_id: str, reason: str):
        super().__init__(
            event_type="UserDeleted",
            bounded_context=BoundedContext.USER_MANAGEMENT,
            category=EventCategory.USER,
            aggregate_id=user_id,
            aggregate_type="User",
            payload={"reason": reason},
        )
