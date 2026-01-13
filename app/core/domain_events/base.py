"""
Core Domain Events Base Classes.

يوفر الفئات الأساسية لنظام الأحداث (Domain Events).

المبادئ:
- Single Responsibility: فقط الفئات الأساسية
- Open/Closed: مفتوحة للتوسع مغلقة للتعديل
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import ClassVar


class EventCategory(Enum):
    """تصنيف الأحداث (Event Categories)."""

    SYSTEM = "system"
    USER = "user"
    MISSION = "mission"
    INTEGRATION = "integration"


class BoundedContext(Enum):
    """السياقات المحددة (Bounded Contexts)."""

    USER_MANAGEMENT = "user_management"
    MISSION_ORCHESTRATION = "mission_orchestration"
    TASK_EXECUTION = "task_execution"
    SECURITY_COMPLIANCE = "security_compliance"
    API_GATEWAY = "api_gateway"
    ADMIN_OPERATIONS = "admin_operations"
    NOTIFICATION_DELIVERY = "notification_delivery"
    ANALYTICS_REPORTING = "analytics_reporting"
    UNKNOWN = "unknown"


@dataclass
class DomainEvent:
    """
    الفئة الأساسية لجميع أحداث النظام (Base class for all domain events).

    المبادئ:
        - Immutable: الأحداث غير قابلة للتغيير
        - Self-describing: كل حدث يصف نفسه
        - Timestamped: كل حدث له طابع زمني
    """

    event_type: str = field(init=True)
    payload: dict[str, object] = field(default_factory=dict)
    event_id: str | None = None
    occurred_at: datetime = field(default_factory=datetime.utcnow)
    bounded_context: BoundedContext = BoundedContext.UNKNOWN
    category: EventCategory = EventCategory.SYSTEM
    aggregate_id: str | None = None
    aggregate_type: str | None = None

    def __post_init__(self):
        """تهيئة الحدث بعد الإنشاء."""
        if self.event_id is None:
            import uuid

            self.event_id = str(uuid.uuid4())
        if not self.event_type:
            self.event_type = self.__class__.__name__


class DomainEventRegistry:
    """
    سجل أحداث النظام (Domain Event Registry).

    يسمح بالتسجيل الديناميكي للأحداث واسترجاعها.
    """

    _registry: ClassVar[dict[str, type[DomainEvent]]] = {}

    @classmethod
    def register(cls, event_class: type[DomainEvent]) -> type[DomainEvent]:
        """تسجيل حدث جديد."""
        cls._registry[event_class.__name__] = event_class
        return event_class

    @classmethod
    def get_event_class(cls, name: str) -> type[DomainEvent] | None:
        """الحصول على فئة حدث بالاسم."""
        return cls._registry.get(name)

    @classmethod
    def list_events(cls) -> list[str]:
        """عرض قائمة بجميع الأحداث المسجلة."""
        return list(cls._registry.keys())
