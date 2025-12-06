import logging
from collections.abc import AsyncGenerator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import Session, sessionmaker

from app.core.engine_factory import (
    DatabaseURLSanitizer,
    create_unified_async_engine,
)

logger = logging.getLogger(__name__)

# --- SINGLETON ENGINE CREATION ---
# We strictly use the factory. No raw create_async_engine calls allowed.
engine = create_unified_async_engine()

# --- SESSION FACTORY (ASYNC) ---
async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Alias for backward compatibility / preference
AsyncSessionLocal = async_session_factory


# =============================================================================
# 🛡️ SCHEMA VALIDATOR — فاحص تطابق Schema التلقائي
# =============================================================================
# يتحقق من تطابق schema الكود مع قاعدة البيانات
# يكتشف الأعمدة المفقودة ويحاول إصلاحها تلقائياً
# =============================================================================

# قائمة الجداول المسموح بها (whitelist للأمان)
_ALLOWED_TABLES = frozenset({"admin_conversations"})

# قائمة الأعمدة المطلوبة لكل جدول
REQUIRED_SCHEMA = {
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


async def validate_and_fix_schema(auto_fix: bool = True) -> dict:
    """
    🔍 التحقق من تطابق Schema وإصلاح المشاكل تلقائياً.

    Args:
        auto_fix: إذا كان True، يحاول إصلاح الأعمدة المفقودة تلقائياً

    Returns:
        dict: نتائج الفحص والإصلاح
    """
    results = {
        "status": "ok",
        "checked_tables": [],
        "missing_columns": [],
        "fixed_columns": [],
        "errors": [],
    }

    try:
        async with engine.connect() as conn:
            for table_name, schema_info in REQUIRED_SCHEMA.items():
                # Security: validate table name against whitelist
                if table_name not in _ALLOWED_TABLES:
                    logger.warning(f"⚠️ Skipping unknown table: {table_name}")
                    continue

                results["checked_tables"].append(table_name)

                # الحصول على الأعمدة الموجودة باستخدام parameterized query
                try:
                    # Check dialect to support both PostgreSQL and SQLite
                    dialect_name = conn.dialect.name
                    if dialect_name == "sqlite":
                        # SQLite PRAGMA doesn't support parameterized queries directly
                        # Use text() with bound parameter for safer execution
                        # Note: table_name is already validated against _ALLOWED_TABLES whitelist
                        result = await conn.execute(
                            text("SELECT * FROM pragma_table_info(:table_name)"),
                            {"table_name": table_name}
                        )
                        # Row format: (cid, name, type, notnull, dflt_value, pk)
                        existing_columns = {row[1] for row in result.fetchall()}
                    else:
                        # Default to PostgreSQL standard information_schema
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
                                    # SQL is predefined, not from user input
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

            # Commit التغييرات
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
    🚀 فحص Schema عند بدء التطبيق.

    يُنفذ تلقائياً عند بدء التطبيق للتأكد من تطابق Schema.
    يحاول إصلاح المشاكل البسيطة تلقائياً.
    """
    logger.info("🔍 Validating database schema...")

    results = await validate_and_fix_schema(auto_fix=True)

    if results["status"] == "ok":
        logger.info("✅ Schema validation passed - all columns present")
    elif results["fixed_columns"]:
        logger.warning(f"⚠️ Schema had issues but was auto-fixed: {results['fixed_columns']}")
    elif results["missing_columns"]:
        missing = ", ".join(results["missing_columns"])
        logger.error(f"❌ CRITICAL: Missing columns could not be fixed: {missing}")
        logger.error("   Run: flask db upgrade OR alembic upgrade head")

    if results["errors"]:
        for error in results["errors"]:
            logger.error(f"   Error: {error}")


# =============================================================================
# 🔧 SYNC SESSION SUPPORT (For Legacy/Background Services)
# =============================================================================
# Some services like master_agent_service.py use synchronous sessions
# for background thread operations. This provides backward compatibility.

_sync_engine = None
_sync_session_factory = None


def _get_sync_engine():
    """Lazily create sync engine only when needed."""
    global _sync_engine
    if _sync_engine is None:
        import os

        db_url = os.getenv("DATABASE_URL")
        db_url = DatabaseURLSanitizer.sanitize(db_url, for_async=False)
        # Convert async URL to sync if needed
        if "postgresql+asyncpg" in db_url:
            db_url = db_url.replace("postgresql+asyncpg", "postgresql")
        elif "sqlite+aiosqlite" in db_url:
            db_url = db_url.replace("sqlite+aiosqlite", "sqlite")

        # Reverse SSL params for psycopg2
        db_url = DatabaseURLSanitizer.reverse_ssl_for_sync(db_url)

        connect_args = {}
        if "sqlite" in db_url:
            connect_args["check_same_thread"] = False

        _sync_engine = create_engine(db_url, connect_args=connect_args, pool_pre_ping=True)
    return _sync_engine


def _get_sync_session_factory():
    """Lazily create sync session factory only when needed."""
    global _sync_session_factory
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
    🔧 COMPATIBILITY LAYER FOR SYNC SESSIONS

    This class provides a sync session factory interface that mimics
    the old Flask-SQLAlchemy SessionLocal pattern. It's used by:
    - master_agent_service.py (background threads)
    - Other legacy sync code

    Usage:
        session = SessionLocal()
        try:
            # do work
            session.commit()
        finally:
            session.close()
    """

    def __new__(cls) -> Session:
        """Create and return a new sync session."""
        factory = _get_sync_session_factory()
        return factory()


@contextmanager
def get_sync_session():
    """Context manager for sync sessions."""
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
    FastAPI dependency to get a database session.
    Ensures sessions are closed after use.
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
