"""
محرك قاعدة البيانات (Database Engine).

يقوم هذا الوحدة بإدارة الاتصال بقاعدة البيانات، وإنشاء الجلسات (Sessions)، والتحقق من المخطط (Schema Validation).
تم تصميمه ليكون قوياً (Robust) وآمناً (Secure) مع دعم البيئات غير المتزامنة (Async) بشكل أساسي.

المعايير المطبقة (Standards Applied):
- CS50 2025: صرامة النوع والتوثيق (Type Strictness & Documentation).
- Singleton Pattern: ضمان وجود محرك واحد.
- Fail-Fast: التحقق من المخطط عند البدء.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import contextmanager
from typing import Any, Final

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker

from app.core.engine_factory import (
    DatabaseURLSanitizer,
    create_unified_async_engine,
)

logger = logging.getLogger(__name__)

__all__ = [
    "AsyncSessionLocal",
    "SessionLocal",
    "async_session_factory",
    "engine",
    "get_db",
    "get_sync_session",
    "validate_schema_on_startup",
]


# --- SINGLETON ENGINE CREATION (إنشاء المحرك المنفرد) ---
# نستخدم المصنع بشكل صارم. لا يُسمح باستدعاء create_async_engine الخام.
engine: Final[AsyncEngine] = create_unified_async_engine()

# --- SESSION FACTORY (ASYNC) (مصنع الجلسات غير المتزامن) ---
# المصنع الأساسي للجلسات المستخدم في جميع أنحاء التطبيق للوصول غير المتزامن لقاعدة البيانات.
async_session_factory: Final[async_sessionmaker[AsyncSession]] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # منع انتهاء صلاحية السمات بعد الالتزام لتقليل الرحلات لقاعدة البيانات
    autocommit=False,        # إدارة المعاملات الصريحة أكثر أماناً
    autoflush=False,         # لا يتم إرسال التغييرات للقاعدة حتى يتم استدعاء flush() أو commit()
)

# اسم مستعار للتوافق مع الأجزاء القديمة من قاعدة الكود (Alias for backward compatibility)
AsyncSessionLocal = async_session_factory


# =============================================================================
# 🛡️ SCHEMA VALIDATOR — فاحص تطابق Schema التلقائي
# =============================================================================

# قائمة الجداول المسموح بها (whitelist للأمان)
_ALLOWED_TABLES: Final[frozenset[str]] = frozenset({"admin_conversations"})

# قائمة الأعمدة المطلوبة لكل جدول
REQUIRED_SCHEMA: Final[dict[str, dict[str, Any]]] = {
    "admin_conversations": {
        "columns": [
            "id",
            "title",
            "user_id",
            "conversation_type",
            "linked_mission_id",
            "created_at",
        ],
        "auto_fix": {
            "linked_mission_id": 'ALTER TABLE "admin_conversations" ADD COLUMN IF NOT EXISTS "linked_mission_id" INTEGER'
        },
        "indexes": {
            "linked_mission_id": 'CREATE INDEX IF NOT EXISTS "ix_admin_conversations_linked_mission_id" ON "admin_conversations"("linked_mission_id")'
        },
    }
}


async def validate_and_fix_schema(auto_fix: bool = True) -> dict[str, Any]:  # noqa: PLR0912
    """
    التحقق من تطابق Schema وإصلاح المشاكل تلقائياً (Schema Validation & Fix).

    يقوم هذا التابع بفحص الجداول المحددة للتأكد من وجود كافة الأعمدة المطلوبة.
    إذا تم تفعيل `auto_fix`، سيحاول تنفيذ استعلامات SQL محددة مسبقاً لإصلاح النقص.

    Args:
        auto_fix (bool): تفعيل محاولة الإصلاح التلقائي للأعمدة المفقودة.

    Returns:
        dict[str, Any]: تقرير بنتائج الفحص والإصلاح (الحالة، الأخطاء، الأعمدة المضافة).
    """
    results: dict[str, Any] = {
        "status": "ok",
        "checked_tables": [],
        "missing_columns": [],
        "fixed_columns": [],
        "errors": [],
    }

    try:
        async with engine.connect() as conn:
            for table_name, schema_info in REQUIRED_SCHEMA.items():
                # أمان: التحقق من اسم الجدول ضد القائمة البيضاء
                if table_name not in _ALLOWED_TABLES:
                    logger.warning(f"⚠️ Skipping unknown table: {table_name}")
                    continue

                results["checked_tables"].append(table_name)

                # الحصول على الأعمدة الموجودة باستخدام استعلام آمن
                try:
                    dialect_name = conn.dialect.name
                    existing_columns: set[str] = set()

                    if dialect_name == "sqlite":
                        # SQLite PRAGMA لا يدعم المعاملات المقيدة (Parameterized) مباشرة
                        # لكن table_name تم التحقق منه مسبقاً ضد القائمة البيضاء
                        result = await conn.execute(
                            text("SELECT * FROM pragma_table_info(:table_name)"),
                            {"table_name": table_name},
                        )
                        # التنسيق: (cid, name, type, notnull, dflt_value, pk)
                        existing_columns = {row[1] for row in result.fetchall()}
                    else:
                        # الافتراضي: معيار PostgreSQL information_schema
                        result = await conn.execute(
                            text(
                                "SELECT column_name FROM information_schema.columns "
                                "WHERE table_name = :table_name"
                            ),
                            {"table_name": table_name},
                        )
                        existing_columns = {row[0] for row in result.fetchall()}
                except Exception as e:
                    results["errors"].append(f"Error checking table {table_name}: {e}")
                    continue

                # التحقق من الأعمدة المطلوبة
                required_columns = set(schema_info.get("columns", []))
                missing = required_columns - existing_columns

                if missing:
                    results["missing_columns"].extend([f"{table_name}.{col}" for col in missing])

                    if auto_fix:
                        # محاولة إصلاح الأعمدة المفقودة (SQL مُعرّف مسبقاً)
                        auto_fix_queries = schema_info.get("auto_fix", {})
                        index_queries = schema_info.get("indexes", {})

                        for col in missing:
                            if col in auto_fix_queries:
                                try:
                                    # SQL آمن ومحدد مسبقاً
                                    await conn.execute(text(auto_fix_queries[col]))
                                    logger.info(f"✅ Added missing column: {table_name}.{col}")
                                    results["fixed_columns"].append(f"{table_name}.{col}")

                                    # إضافة الفهرس إذا كان موجوداً
                                    if col in index_queries:
                                        await conn.execute(text(index_queries[col]))
                                        logger.info(f"✅ Created index for: {table_name}.{col}")

                                except Exception as e:
                                    error_msg = f"Failed to fix {table_name}.{col}: {e}"
                                    logger.error(f"❌ {error_msg}")
                                    results["errors"].append(error_msg)

            # تثبيت التغييرات (Commit) إذا تم إصلاح شيء
            if results["fixed_columns"]:
                await conn.commit()

    except Exception as e:
        results["status"] = "error"
        results["errors"].append(f"Schema validation failed: {e}")
        logger.error(f"❌ Schema validation error: {e}")

    # تحديد الحالة النهائية
    if results["errors"]:
        results["status"] = "error"
    elif results["missing_columns"] and not results["fixed_columns"]:
        results["status"] = "warning"

    return results


async def validate_schema_on_startup() -> None:
    """
    فحص Schema عند بدء التطبيق (Startup Schema Check).

    يُنفذ تلقائياً عند بدء تشغيل النواة للتأكد من سلامة هيكل قاعدة البيانات.
    """
    logger.info("🔍 Validating database schema... (جاري فحص مخطط قاعدة البيانات)")

    results = await validate_and_fix_schema(auto_fix=True)

    if results["status"] == "ok":
        logger.info("✅ Schema validation passed - all columns present (المخطط سليم)")
    elif results["fixed_columns"]:
        logger.warning(f"⚠️ Schema had issues but was auto-fixed: {results['fixed_columns']}")
    elif results["missing_columns"]:
        missing = ", ".join(results["missing_columns"])
        logger.error(f"❌ CRITICAL: Missing columns could not be fixed: {missing}")
        logger.error("   Run: alembic upgrade head")

    if results["errors"]:
        for error in results["errors"]:
            logger.error(f"   Error: {error}")


# =============================================================================
# 🔧 SYNC SESSION SUPPORT (For Legacy/Background Services)
# =============================================================================
# توفر هذه الطبقة توافقية مع الخدمات التي تعمل في الخلفية أو تستخدم خيوطاً متزامنة.

_sync_engine = None
_sync_session_factory = None


def _get_sync_engine() -> Any:
    """إنشاء المحرك المتزامن بكسل (Lazily) عند الحاجة فقط."""
    global _sync_engine  # noqa: PLW0603
    if _sync_engine is None:
        from app.config.settings import get_settings  # noqa: PLC0415

        # التوجيه الذكي: استخدام التكوين المركزي
        settings = get_settings()
        db_url = str(settings.DATABASE_URL)

        # استخدام المعقم للتحويل إلى الوضع المتزامن
        db_url = DatabaseURLSanitizer.sanitize(db_url, for_async=False)

        # تحويل عناوين Async إلى Sync يدوياً إذا لزم الأمر
        if "postgresql+asyncpg" in db_url:
            db_url = db_url.replace("postgresql+asyncpg", "postgresql")
        elif "sqlite+aiosqlite" in db_url:
            db_url = db_url.replace("sqlite+aiosqlite", "sqlite")

        # عكس إعدادات SSL لـ psycopg2
        db_url = DatabaseURLSanitizer.reverse_ssl_for_sync(db_url)

        connect_args = {}
        if "sqlite" in db_url:
            connect_args["check_same_thread"] = False

        _sync_engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
    return _sync_engine


def _get_sync_session_factory() -> sessionmaker[Session]:
    """إنشاء مصنع الجلسات المتزامن بكسل (Lazily)."""
    global _sync_session_factory  # noqa: PLW0603
    if _sync_session_factory is None:
        _sync_session_factory = sessionmaker(
            bind=_get_sync_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _sync_session_factory


class SessionLocal:
    """
    طبقة التوافق للجلسات المتزامنة (Sync Compatibility Layer).

    توفر واجهة لإنشاء جلسات متزامنة تحاكي الأنماط القديمة.
    الاستخدام:
        session = SessionLocal()
        try:
            # do work
            session.commit()
        finally:
            session.close()
    """

    def __new__(cls) -> Session:
        """إنشاء وإرجاع جلسة متزامنة جديدة."""
        factory = _get_sync_session_factory()
        return factory()


@contextmanager
def get_sync_session() -> Any:
    """
    مدير سياق للجلسات المتزامنة (Context Manager).

    يضمن فتح الجلسة، والالتزام بالتغييرات (Commit)، أو التراجع عند الخطأ (Rollback)،
    ثم الإغلاق الآمن.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    حاقن التبعية لجلسات قاعدة البيانات (Dependency Injection Provider).

    مصمم للاستخدام مع `Depends()` في مسارات FastAPI.
    يضمن:
    1. إنشاء جلسة جديدة لكل طلب.
    2. إغلاق الجلسة بأمان حتى في حالة حدوث أخطاء.
    3. التراجع التلقائي عن المعاملات (Rollback) عند الاستثناءات.

    Yields:
        AsyncSession: جلسة نشطة جاهزة للاستخدام.
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e!s}")
            await session.rollback()
            raise
        finally:
            await session.close()
