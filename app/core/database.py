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

# TODO: Split this function (53 lines) - KISS principle
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
        "pool_recycle": 1800,    # إعادة تدوير الاتصال كل 30 دقيقة
    }

    # تخصيص إعدادات SQLite
    if "sqlite" in db_url:
        # SQLite يحتاج إعدادات خاصة للمسارات
        engine_args["connect_args"] = {"check_same_thread": False}
        logger.info("🔌 Database: SQLite (Local/Testing Mode)")
    else:
        # إعدادات خاصة بـ Postgres

        # 1. إعدادات حجم المسبح (Connection Pool)
        # ⚠️ CRITICAL: تقليل حجم المسبح في بيئات التطوير لمنع انهيار الذاكرة (OOM Kill)
        if settings.ENVIRONMENT == "development" or settings.CODESPACES:
            logger.info("🔧 Development/Codespaces mode detected: Reducing DB pool size to prevent OOM.")
            engine_args["pool_size"] = 5      # عدد اتصالات قليل
            engine_args["max_overflow"] = 10  # زيادة محدودة
        else:
            engine_args["pool_size"] = settings.DB_POOL_SIZE
            engine_args["max_overflow"] = settings.DB_MAX_OVERFLOW

        # 2. إعدادات التوافقية (Compatibility Settings)
        # ⚠️ CRITICAL FIX: تعطيل prepared statements نهائياً
        # هذا ضروري جداً للتوافق مع Supabase Transaction Pooler (PgBouncer)
        # وبدون هذا الإعداد سينهار النظام مع خطأ: prepared statement "..." does not exist
        # نستخدم setdefault للتأكد من عدم مسح أي إعدادات سابقة عن طريق الخطأ، ولكن هنا نحن ننشئ القاموس
        engine_args["connect_args"] = {
            "statement_cache_size": 0,  # Disable prepared statements for AsyncPG
            "prepared_statement_cache_size": 0, # Redundant safety for some SQLAlchemy versions
        }

        logger.info(f"🔌 Connecting to Postgres Database: {settings.ENVIRONMENT}")
        logger.warning("   -> Prepared Statements: DISABLED (PgBouncer Strict Compatibility Mode)")

    # 🛑 LOGGING THE FINAL CONFIGURATION FOR DEBUGGING
    # هذا السطر مهم جداً للتأكد من أن الإعدادات وصلت للمحرك بشكل صحيح
    logger.debug(f"   -> Final Engine Args: {engine_args}")

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
