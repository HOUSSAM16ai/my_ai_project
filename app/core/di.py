"""
حاوية حقن التبعيات والواجهة الموحّدة.
-----------------------------------
يوفّر هذا الملف سجلًا مركزيًا للتبعيات وفق مبدأ عكس الاعتماد (DIP)، مع دوال
واجهة تحافظ على التوافق مع المكوّنات الأساسية القديمة.

يعتمد التصميم على حاوية بسيطة قابلة للتوسّع مع إعادة تصدير الخدمات الأساسية.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Annotated, ClassVar, TypeVar, cast

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

if TYPE_CHECKING:
    from app.application.services import DefaultHealthCheckService
    from app.services.kagent.interface import KagentMesh
    from app.services.system.system_service import SystemService

# --- Legacy / Core Re-exports ---
from app.core.config import get_settings
from app.core.database import get_db
from app.core.database import get_db as get_session  # Alias for backward compatibility
from app.core.logging import get_logger

# --- Facade Functions for Legacy Routers ---


def get_system_service() -> SystemService:
    """إرجاع خدمة النظام الأساسية مع الحفاظ على التوافق الخلفي."""
    from app.services.system.system_service import system_service

    return system_service


async def get_health_check_service(
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DefaultHealthCheckService:
    """بناء خدمة فحص الصحة باستخدام المستودع المعتمد على قاعدة البيانات."""
    from app.application.services import DefaultHealthCheckService
    from app.infrastructure.repositories.database_repository import SQLAlchemyDatabaseRepository

    repo = SQLAlchemyDatabaseRepository(db)
    return DefaultHealthCheckService(repo)


# --- New DI Container (SOLID) ---

T = TypeVar("T")


class Container:
    """
    حاوية بسيطة لحقن التبعيات تضمن الالتزام بمبدأ عكس الاعتماد (DIP).
    """

    _factories: ClassVar[dict[type[object], Callable[[], object]]] = {}
    _singletons: ClassVar[dict[type[object], object]] = {}

    @classmethod
    def register(cls, interface: type[T], factory: Callable[[], T]) -> None:
        """
        تسجيل مُنشئ للتبعيات لنوع محدّد.
        يتم تنفيذ المُنشئ عند كل عملية حل (Transient).
        """
        cls._factories[interface] = factory

    @classmethod
    def register_singleton(cls, interface: type[T], instance: T) -> None:
        """
        تسجيل نسخة مفردة (Singleton) لواجهة معيّنة.
        """
        cls._singletons[interface] = instance

    @classmethod
    def register_singleton_factory(
        cls,
        interface: type[T],
        factory: Callable[[], T],
    ) -> None:
        """
        تسجيل مُنشئ كسول يُستدعى مرة واحدة ثم يُخزّن (Lazy Singleton).
        """

        def lazy_wrapper() -> object:
            if interface not in cls._singletons:
                cls._singletons[interface] = factory()
            return cls._singletons[interface]

        cls._factories[interface] = lazy_wrapper

    @classmethod
    def resolve(cls, interface: type[T]) -> T:
        """
        حلّ التبعية لواجهة معيّنة وإرجاع النسخة المناسبة.
        """
        if interface in cls._singletons:
            return cast(T, cls._singletons[interface])

        if interface in cls._factories:
            return cast(T, cls._factories[interface]())

        raise ValueError(f"No registration found for {interface.__name__}")

    @classmethod
    def clear(cls) -> None:
        """تفريغ الحاوية بالكامل (مفيد للاختبارات)."""
        cls._factories.clear()
        cls._singletons.clear()


# Explicitly export legacy items to satisfy linter regarding "unused import" if they are part of API
__all__ = [
    "Container",
    "get_db",
    "get_health_check_service",
    "get_kagent_mesh",
    "get_logger",
    "get_session",
    "get_settings",
    "get_system_service",
]


def get_kagent_mesh() -> KagentMesh:
    """جلب شبكة الوكيل الذكي عبر الحاوية."""
    from app.services.kagent.interface import KagentMesh

    return Container.resolve(KagentMesh)


# Bootstrap Kagent as a Lazy Singleton
def _create_kagent_mesh() -> KagentMesh:
    """إنشاء نسخة جديدة من شبكة الوكيل الذكي."""
    from app.services.kagent.interface import KagentMesh

    return KagentMesh()


from app.services.kagent.interface import KagentMesh

Container.register_singleton_factory(KagentMesh, _create_kagent_mesh)
