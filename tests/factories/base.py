"""مصانع خفيفة الوزن لإنشاء كائنات النماذج داخل الاختبارات بدون تبعيات إضافية."""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Callable

from app.core.domain.models import Mission, User

_email_counter = itertools.count(1)


def _next_email() -> str:
    return f"user{next(_email_counter)}@example.com"


@dataclass
class UserFactory:
    """منشئ كائنات المستخدمين بقيم افتراضية قابلة للتخصيص."""

    email: Callable[[], str] = _next_email
    full_name: Callable[[], str] = lambda: "Test User"
    is_admin: bool = False

    def build(self, **overrides: object) -> User:
        """بناء كائن مستخدم جديد مع تطبيق أي قيم مخصصة."""

        email_value = overrides.pop("email", self.email())
        full_name_value = overrides.pop("full_name", self.full_name())
        is_admin_value = bool(overrides.pop("is_admin", self.is_admin))
        user = User(email=email_value, full_name=full_name_value, is_admin=is_admin_value)
        password = overrides.pop("password", None)
        if password:
            user.set_password(str(password))
        return user


@dataclass
class MissionFactory:
    """منشئ مهام بسيط مع قيم افتراضية موحدة."""

    objective: Callable[[], str] = lambda: "Test Mission"

    def build(self, **overrides: object) -> Mission:
        """إرجاع مهمة SQLModel جاهزة للحفظ في قاعدة البيانات."""

        objective_value = overrides.pop("objective", self.objective())
        initiator_id = overrides.pop("initiator_id", None)
        mission = Mission(objective=objective_value, initiator_id=initiator_id)
        return mission


__all__ = ["UserFactory", "MissionFactory"]
