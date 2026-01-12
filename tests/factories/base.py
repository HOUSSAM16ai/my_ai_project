"""
مصانع الكيانات الأساسية للاختبارات الوظيفية.

توفر هذه الوحدة طرقاً متناسقة لبناء كائنات المجالات الأساسية مع قيم
افتراضية معقولة، بهدف تسريع كتابة الاختبارات وضمان استقرار البيانات
عبر السيناريوهات دون الحاجة إلى ORM معقد أو تكامل مع factory_boy.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from app.core.domain.models import Mission, MissionStatus, User


@dataclass
class _Sequence:
    """مولد أرقام متسلسلة قابل للحقن لتسهيل تتبع البيانات في الاختبارات."""

    start: int = 0

    def next(self) -> int:
        """إرجاع الرقم الحالي ثم زيادته للحفاظ على التفرد."""

        current = self.start
        self.start += 1
        return current


class UserFactory:
    """مصنع إنشاء مستخدمين بتسميات وأسماء بريدية فريدة لضمان ثبات الاختبارات."""

    def __init__(self, sequencer: _Sequence | None = None):
        self._sequencer = sequencer or _Sequence()

    def build(
        self,
        *,
        full_name: str | None = None,
        email: str | None = None,
        is_admin: bool = False,
        password: str | None = None,
    ) -> User:
        """إنشاء كائن مستخدم جديد مع تعيين كلمة مرور اختيارية."""

        index = self._sequencer.next()
        user = User(
            full_name=full_name or f"Test User {index}",
            email=email or f"user{index}@example.com",
            is_admin=is_admin,
        )
        if password:
            user.set_password(password)
        return user


class MissionFactory:
    """مصنع مهام يضبط القيم الافتراضية وفق حالات العمل الشائعة."""

    def __init__(
        self,
        sequencer: _Sequence | None = None,
        objective_generator: Callable[[int], str] | None = None,
    ):
        self._sequencer = sequencer or _Sequence()
        self._objective_generator = objective_generator or (lambda idx: f"Mission Objective {idx}")

    def build(
        self,
        *,
        initiator_id: int,
        objective: str | None = None,
        status: MissionStatus | str | None = None,
    ) -> Mission:
        """إنشاء كائن مهمة جديد مع دعم تحويل حالة المهمة النصية إلى Enum."""

        index = self._sequencer.next()
        resolved_status = (
            MissionStatus(status) if isinstance(status, str) else status or MissionStatus.PENDING
        )
        return Mission(
            objective=objective or self._objective_generator(index),
            status=resolved_status,
            initiator_id=initiator_id,
        )


__all__ = ["MissionFactory", "UserFactory"]
