"""
نماذج بيانات ناقل الأحداث (Event Bus Models).

تُعرّف هذه الوحدة هيكلية الأحداث وأنواع البيانات المرتبطة بها.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class Event:
    """
    حدث في النظام.

    Attributes:
        event_id: معرف فريد للحدث
        event_type: نوع الحدث
        payload: بيانات الحدث
        timestamp: وقت الحدث
        source: مصدر الحدث
        correlation_id: معرف الارتباط للتتبع
    """

    event_id: UUID
    event_type: str
    payload: dict[str, object]
    timestamp: datetime
    source: str
    correlation_id: UUID | None = None
