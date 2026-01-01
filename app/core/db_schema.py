"""
مدقق مخطط قاعدة البيانات (Database Schema Validator).

هذا الملف مسؤول عن التحقق من صحة جداول قاعدة البيانات وإصلاحها تلقائياً عند بدء التشغيل.
تم فصله عن `database.py` تطبيقاً لمبدأ المسؤولية الواحدة (SRP).

المعايير (Standards):
- CS50 2025: توثيق عربي شامل.
- Fail-Fast: كشف الأخطاء مبكراً.
"""

from typing import Any

import logging
from typing import Final

from sqlalchemy import text

from app.core.database import engine

logger = logging.getLogger(__name__)

__all__ = ["validate_schema_on_startup"]

# =============================================================================
# 🛡️ إعدادات المخطط (Schema Configuration)
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

async def _get_existing_columns(conn: dict[str, str | int | bool], table_name: str) -> set[str]:
    """استخراج أسماء الأعمدة الموجودة في الجدول."""
    dialect_name = conn.dialect.name

    if dialect_name == "sqlite":
        result = await conn.execute(
            text("SELECT * FROM pragma_table_info(:table_name)"),
            {"table_name": table_name},
        )
        return {row[1] for row in result.fetchall()}

    result = await conn.execute(
        text(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = :table_name"
        ),
        {"table_name": table_name},
    )
    return {row[0] for row in result.fetchall()}

async def _fix_missing_column(
    conn: dict[str, str | int | bool],
    table_name: str,
    col: str,
    auto_fix_queries: dict[str, str],
    index_queries: dict[str, str]
) -> bool:
    """إصلاح عمود مفقود وإنشاء الفهرس إن وجد."""
    if col not in auto_fix_queries:
        return False

    try:
        await conn.execute(text(auto_fix_queries[col]))
        logger.info(f"✅ Added missing column: {table_name}.{col}")

        if col in index_queries:
            await conn.execute(text(index_queries[col]))
            logger.info(f"✅ Created index for: {table_name}.{col}")

        return True
    except Exception as e:
        logger.error(f"❌ Failed to fix {table_name}.{col}: {e}")
        return False

async def validate_and_fix_schema(auto_fix: bool = True) -> dict[str, Any]:
    """
    التحقق من تطابق Schema وإصلاح المشاكل تلقائياً.

    Args:
        auto_fix (bool): تفعيل محاولة الإصلاح التلقائي.

    Returns:
        dict[str, Any]: تقرير بالنتيجة.
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
                if table_name not in _ALLOWED_TABLES:
                    continue

                results["checked_tables"].append(table_name)

                try:
                    existing_columns = await _get_existing_columns(conn, table_name)
                except Exception as e:
                    results["errors"].append(f"Error checking table {table_name}: {e}")
                    continue

                required_columns = set(schema_info.get("columns", []))
                missing = required_columns - existing_columns

                if missing:
                    results["missing_columns"].extend([f"{table_name}.{col}" for col in missing])

                    if auto_fix:
                        auto_fix_queries = schema_info.get("auto_fix", {})
                        index_queries = schema_info.get("indexes", {})

                        for col in missing:
                            if await _fix_missing_column(conn, table_name, col, auto_fix_queries, index_queries):
                                results["fixed_columns"].append(f"{table_name}.{col}")

            if results["fixed_columns"]:
                await conn.commit()

    except Exception as e:
        results["status"] = "error"
        results["errors"].append(f"Schema validation failed: {e}")
        logger.error(f"❌ Schema validation error: {e}")

    if results["errors"]:
        results["status"] = "error"
    elif results["missing_columns"] and not results["fixed_columns"]:
        results["status"] = "warning"

    return results

async def validate_schema_on_startup() -> None:
    """
    فحص Schema عند بدء التطبيق.
    """
    logger.info("🔍 Validating database schema... (جاري فحص مخطط قاعدة البيانات)")

    results = await validate_and_fix_schema(auto_fix=True)

    if results["status"] == "ok":
        logger.info("✅ Schema validation passed (المخطط سليم)")
    elif results["fixed_columns"]:
        logger.warning(f"⚠️ Schema auto-fixed: {results['fixed_columns']}")
    elif results["missing_columns"]:
        logger.error(f"❌ CRITICAL: Missing columns: {results['missing_columns']}")

    if results["errors"]:
        for error in results["errors"]:
            logger.error(f"   Error: {error}")
