"""
واجهات خدمات التطبيق (Protocols) وفق مبدأ الانعكاس في الاعتماد.

تضمن هذه الواجهات أن الطبقات العليا تتعامل مع عقود مكتوبة بدل تنفيذات
ملموسة، مع توثيق عربي صارم وإزالة أي اعتماد على النوع `object` لضمان وضوح
العقود.
"""

from __future__ import annotations

from typing import Protocol, TypedDict


class DatabaseHealth(TypedDict):
    """
    تمثيل صحي لوضع قاعدة البيانات.

    Attributes:
        connected: حالة الاتصال الفعلي.
        status: وصف بشري مختصر للحالة (ok أو error).
        error: رسالة الخطأ إن وجدت، أو None عند النجاح.
    """

    connected: bool
    status: str
    error: str | None


class SystemHealth(TypedDict):
    """التقرير الصحي العام للنظام شاملاً حالة قاعدة البيانات."""

    status: str
    database: DatabaseHealth


class SystemInfo(TypedDict):
    """ملخص معلومات النظام المعروضة للمستهلكين."""

    name: str
    version: str
    status: str


class UserProfile(TypedDict):
    """عرض عام لبيانات المستخدم المسموح بإرجاعها عبر الـ API."""

    id: int
    email: str
    is_admin: bool


class UserCreationPayload(TypedDict):
    """
    حمولة إنشاء مستخدم جديد.

    Attributes:
        full_name: الاسم الكامل للمستخدم.
        email: البريد الإلكتروني بصيغة قياسية.
        password: كلمة المرور النصية قبل التشفير.
        is_admin: علم يحدد صلاحيات المسؤول.
    """

    full_name: str
    email: str
    password: str
    is_admin: bool


class HealthCheckService(Protocol):
    """واجهة فحص صحة النظام."""

    async def check_system_health(self) -> SystemHealth:
        """يرجع تقريرًا صحيًا شاملًا."""
        ...

    async def check_database_health(self) -> DatabaseHealth:
        """يتحقق من اتصال قاعدة البيانات ويعيد تفاصيل مفهومة."""
        ...


class SystemService(Protocol):
    """واجهة خدمات النظام العامة."""

    async def get_system_info(self) -> SystemInfo:
        """يرجع معلومات ثابتة حول هوية النظام وإصداره."""
        ...

    async def verify_integrity(self) -> SystemHealth:
        """يتحقق من سلامة مكونات النظام الأساسية."""
        ...


class UserService(Protocol):
    """واجهة إدارة المستخدمين."""

    async def get_user_by_id(self, user_id: int) -> UserProfile | None:
        """يجلب مستخدمًا بناءً على المعرّف الأساسي."""
        ...

    async def authenticate_user(self, email: str, password: str) -> UserProfile | None:
        """يعيد ملخص المستخدم عند نجاح التحقق من الهوية."""
        ...

    async def create_user(self, user_data: UserCreationPayload) -> UserProfile:
        """ينشئ مستخدمًا جديدًا ويعيد ملخصه المسموح به."""
        ...
