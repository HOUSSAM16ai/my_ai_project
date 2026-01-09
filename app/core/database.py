"""
محرك قاعدة البيانات (Database Engine) - قلب البيانات.

هذا الملف هو المسؤول الوحيد عن إنشاء وإدارة الاتصال بقاعدة البيانات في النظام.
تم تبسيطه ليكون مفهوماً للمطورين المبتدئين، مع الالتزام بمبادئ Clean Code.

المبادئ (Principles):
- SRP: مسؤول فقط عن الاتصال وإنشاء الجلسات.
- KISS: استخدام مباشر للمكتبات القياسية بدون تعقيدات زائدة.
- Async First: النظام مصمم ليعمل بشكل غير متزامن للحصول على أعلى أداء.
- CS61: Connection pooling, memory management, performance profiling.
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

from app.core.config import get_settings

logger = logging.getLogger(__name__)

__all__ = [
    "async_session_factory",
    "engine",
    "get_db",
]

def _create_engine() -> AsyncEngine:
    """
    إنشاء محرك قاعدة البيانات.
    Create database engine.

    يستخدم إعدادات التطبيق لإنشاء اتصال آمن وفعال.
    Uses application settings to create a safe and efficient connection.
    """
    settings = get_settings()
    db_url = str(settings.DATABASE_URL)

    # Build engine configuration
    engine_args = _build_base_engine_args(settings)
    
    # Apply database-specific settings
    if "sqlite" in db_url:
        _configure_sqlite_args(engine_args)
    else:
        _configure_postgres_args(engine_args, settings)

    _log_engine_configuration(engine_args)
    return create_async_engine(db_url, **engine_args)


def _build_base_engine_args(settings) -> dict:
    """
    Build base engine arguments.
    بناء المعاملات الأساسية للمحرك.
    """
    return {
        "echo": settings.DEBUG,  # طباعة استعلامات SQL في وضع التطوير
        "pool_pre_ping": True,   # التحقق من صحة الاتصال قبل استخدامه
        "pool_recycle": 1800,    # إعادة تدوير الاتصال كل 30 دقيقة
    }


def _configure_sqlite_args(engine_args: dict) -> None:
    """
    Configure SQLite-specific settings.
    تكوين إعدادات SQLite الخاصة.
    """
    engine_args["connect_args"] = {"check_same_thread": False}
    logger.info("🔌 Database: SQLite (Local/Testing Mode)")


def _configure_postgres_args(engine_args: dict, settings) -> None:
    """
    Configure PostgreSQL-specific settings.
    تكوين إعدادات PostgreSQL الخاصة.
    """
    # Connection pool settings
    _set_postgres_pool_size(engine_args, settings)
    
    # Compatibility settings for PgBouncer
    _set_postgres_compatibility(engine_args)
    
    logger.info(f"🔌 Connecting to Postgres Database: {settings.ENVIRONMENT}")
    logger.warning("   -> Prepared Statements: DISABLED (PgBouncer Strict Compatibility Mode)")


def _set_postgres_pool_size(engine_args: dict, settings) -> None:
    """
    Set PostgreSQL connection pool size based on environment.
    تعيين حجم مسبح اتصالات PostgreSQL بناءً على البيئة.
    """
    # ⚠️ CRITICAL: Reduce pool size in development to prevent OOM Kill
    if settings.ENVIRONMENT == "development" or settings.CODESPACES:
        logger.info("🔧 Development/Codespaces mode detected: Reducing DB pool size to prevent OOM.")
        engine_args["pool_size"] = 5      # Small connection count
        engine_args["max_overflow"] = 10  # Limited overflow
    else:
        engine_args["pool_size"] = settings.DB_POOL_SIZE
        engine_args["max_overflow"] = settings.DB_MAX_OVERFLOW


def _set_postgres_compatibility(engine_args: dict) -> None:
    """
    Set PostgreSQL compatibility settings for PgBouncer.
    تعيين إعدادات التوافق مع PgBouncer.
    
    ⚠️ CRITICAL FIX: Disable prepared statements completely.
    This is essential for compatibility with Supabase Transaction Pooler (PgBouncer).
    Without this setting, the system will crash with error: prepared statement "..." does not exist
    """
    engine_args["connect_args"] = {
        "statement_cache_size": 0,  # Disable prepared statements for AsyncPG
        "prepared_statement_cache_size": 0,  # Redundant safety for some SQLAlchemy versions
    }


def _log_engine_configuration(engine_args: dict) -> None:
    """
    Log final engine configuration for debugging.
    تسجيل تكوين المحرك النهائي للتصحيح.
    """
    logger.debug(f"   -> Final Engine Args: {engine_args}")

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
