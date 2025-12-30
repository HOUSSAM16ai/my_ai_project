"""
محرك قاعدة البيانات (Database Engine) - قلب البيانات.

هذا الملف هو المسؤول الوحيد عن إنشاء وإدارة الاتصال بقاعدة البيانات في النظام.
تم تبسيطه ليكون مفهوماً للمطورين المبتدئين، مع الالتزام بمبادئ Clean Code.

المبادئ (Principles):
- SRP: مسؤول فقط عن الاتصال وإنشاء الجلسات.
- KISS: استخدام مباشر للمكتبات القياسية بدون تعقيدات زائدة.
- Async First: النظام مصمم ليعمل بشكل غير متزامن للحصول على أعلى أداء.
"""

import logging
from collections.abc import AsyncGenerator
from typing import Final

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config.settings import get_settings

logger = logging.getLogger(__name__)

__all__ = [
    "async_session_factory",
    "engine",
    "get_db",
]


def _create_engine() -> AsyncEngine:
    """
    إنشاء محرك قاعدة البيانات.

    يستخدم إعدادات التطبيق لإنشاء اتصال آمن وفعال.
    """
    settings = get_settings()

    # تحضير الرابط
    db_url = str(settings.DATABASE_URL)

    # إعدادات المحرك
    engine_args = {
        "echo": settings.DEBUG,  # طباعة استعلامات SQL في وضع التطوير
        "pool_pre_ping": True,   # التحقق من صحة الاتصال قبل استخدامه
    }

    # تخصيص إعدادات SQLite
    if "sqlite" in db_url:
        # SQLite يحتاج إعدادات خاصة للمسارات
        engine_args["connect_args"] = {"check_same_thread": False}
    else:
        # إعدادات خاصة بـ Postgres (Pool Size)
        # نستخدم قيماً محافظة للبدء
        engine_args["pool_size"] = 10
        engine_args["max_overflow"] = 20
        # Fix for Supabase Transaction Pooler (pgbouncer)
        # Disabling prepared statements is required for transaction pooling
        engine_args["connect_args"] = {"statement_cache_size": 0}

    logger.info(f"🔌 Connecting to database: {settings.ENVIRONMENT} mode")

    return create_async_engine(db_url, **engine_args)


# 1. إنشاء المحرك (The Engine)
engine: Final[AsyncEngine] = _create_engine()


# 2. مصنع الجلسات (Session Factory)
async_session_factory: Final[async_sessionmaker[AsyncSession]] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# 3. حاقن التبعية (Dependency Injection)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    مزود جلسات قاعدة البيانات (Database Session Provider).

    يستخدم هذا التابع في موجهات FastAPI (Routers) للحصول على اتصال آمن بقاعدة البيانات.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"❌ Database session error: {e!s}")
            await session.rollback()
            raise
        finally:
            await session.close()
