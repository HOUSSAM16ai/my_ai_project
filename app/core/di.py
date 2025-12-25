"""
حقن التبعيات (Dependency Injection) - العمود الفقري للنظام.
---------------------------------------------------------
يتبع هذا الملف نمط "Composition Root" لتجميع مكونات النظام.
يعتمد على دوال المصنع (Factory Functions) بدلاً من الفئات لتقليل التعقيد.

المعايير:
- Explicit Dependencies: التبعيات واضحة في التوقيع.
- Interface Segregation: الاعتماد على البروتوكولات وليس التطبيقات.
- MIT 6.0001: التجريد الهيكلي.
"""

from collections.abc import AsyncGenerator
from typing import Final, TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import AppSettings
from app.config.settings import get_settings as _get_settings_config
from app.core.database import async_session_factory
from app.core.logging import get_logger as _get_logger

if TYPE_CHECKING:
    from app.core.protocols import HealthCheckService, SystemService

# Singleton Instances
_SETTINGS_SINGLETON: Final[AppSettings] = _get_settings_config()

__all__ = [
    "get_di_settings",
    "get_settings",
    "get_di_db",
    "get_session",
    "get_db",
    "get_logger",
    "get_health_check_service",
    "get_system_service",
]

def get_di_settings() -> AppSettings:
    """
    استرجاع إعدادات التطبيق (Singleton).
    """
    return _SETTINGS_SINGLETON


get_settings = get_di_settings


async def get_di_db() -> AsyncGenerator[AsyncSession, None]:
    """
    موفر جلسة قاعدة البيانات المتوافقة مع حقن التبعيات.
    يدير دورة حياة الجلسة (Open -> Yield -> Close).
    """
    async with async_session_factory() as session:
        yield session


get_session = get_di_db
get_db = get_di_db
get_logger = _get_logger


# ==============================================================================
# Application Service Dependencies (Clean Architecture)
# ==============================================================================

async def get_health_check_service() -> AsyncGenerator['HealthCheckService', None]:
    """
    الحصول على خدمة فحص الصحة.
    تستخدم Lazy Import لتجنب الدورات (Circular Imports).
    """
    from app.application.services import DefaultHealthCheckService
    from app.infrastructure.repositories import SQLAlchemyDatabaseRepository

    async with async_session_factory() as session:
        db_repo = SQLAlchemyDatabaseRepository(session)
        yield DefaultHealthCheckService(db_repo)


async def get_system_service() -> AsyncGenerator['SystemService', None]:
    """
    الحصول على خدمة النظام.
    """
    from app.application.services import DefaultSystemService
    from app.infrastructure.repositories import SQLAlchemyDatabaseRepository

    async with async_session_factory() as session:
        db_repo = SQLAlchemyDatabaseRepository(session)
        yield DefaultSystemService(db_repo)
