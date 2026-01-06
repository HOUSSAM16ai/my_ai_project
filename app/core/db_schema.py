"""مدقق مخطط قاعدة البيانات (Database Schema Validator).

هذا الملف مسؤول عن التحقق من صحة جداول قاعدة البيانات وإصلاحها تلقائياً عند بدء التشغيل.
تم فصله عن `database.py` تطبيقاً لمبدأ المسؤولية الواحدة (SRP).

المعايير (Standards):
- CS50 2025: توثيق عربي شامل.
- Fail-Fast: كشف الأخطاء مبكراً.
"""

import logging
import re
from typing import Final, NotRequired, TypedDict

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.database import engine

logger = logging.getLogger(__name__)

__all__ = ["validate_schema_on_startup"]

# =============================================================================
# 🛡️ إعدادات المخطط (Schema Configuration)
# =============================================================================

# قائمة الجداول المسموح بها (whitelist للأمان)
_ALLOWED_TABLES: Final[frozenset[str]] = frozenset({"admin_conversations", "users"})

# قائمة الأعمدة المطلوبة لكل جدول
class TableSchemaConfig(TypedDict):
    """تعريف المخطط المطلوب لجدول قاعدة البيانات."""

    columns: list[str]
    auto_fix: dict[str, str]
    indexes: dict[str, str]
    index_names: NotRequired[dict[str, str]]


class SchemaValidationResult(TypedDict):
    """نتيجة فحص المخطط مع تفاصيل الإصلاحات والأخطاء."""

    status: str
    checked_tables: list[str]
    missing_columns: list[str]
    fixed_columns: list[str]
    missing_indexes: list[str]
    fixed_indexes: list[str]
    errors: list[str]


REQUIRED_SCHEMA: Final[dict[str, TableSchemaConfig]] = {
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
        "index_names": {"linked_mission_id": "ix_admin_conversations_linked_mission_id"},
    },
    "users": {
        "columns": [
            "id",
            "external_id",
            "full_name",
            "email",
            "password_hash",
            "is_admin",
            "is_active",
            "status",
            "created_at",
            "updated_at",
        ],
        "auto_fix": {
            "external_id": 'ALTER TABLE "users" ADD COLUMN IF NOT EXISTS "external_id" VARCHAR(36)',
            "is_active": 'ALTER TABLE "users" ADD COLUMN IF NOT EXISTS "is_active" BOOLEAN NOT NULL DEFAULT TRUE',
            "status": 'ALTER TABLE "users" ADD COLUMN IF NOT EXISTS "status" VARCHAR(50) NOT NULL DEFAULT \'active\''
        },
        "indexes": {
            "external_id": 'CREATE UNIQUE INDEX IF NOT EXISTS "ix_users_external_id" ON "users"("external_id")'
        },
        "index_names": {"external_id": "ix_users_external_id"},
    }
}

async def _get_existing_columns(conn: AsyncConnection, table_name: str) -> set[str]:
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
    conn: AsyncConnection,
    table_name: str,
    col: str,
    auto_fix_queries: dict[str, str],
    index_queries: dict[str, str],
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

def _infer_index_name(index_query: str) -> str | None:
    """استنتاج اسم الفهرس من جملة SQL عند غياب التسمية الصريحة.

    يتم استخدام هذا التابع كاحتياط لضمان إنشاء الفهرس حتى لو لم يتم توفير
    الاسم بشكل يدوي في الإعدادات.
    """
    pattern = re.compile(r"INDEX(?: IF NOT EXISTS)?\s+\"([^\"]+)\"", flags=re.IGNORECASE)
    match = pattern.search(index_query)
    if match:
        return match.group(1)
    return None

async def _get_existing_indexes(conn: AsyncConnection, table_name: str) -> set[str]:
    """جلب أسماء الفهارس الموجودة في الجدول لتفادي إنشائها مرتين."""
    dialect_name = conn.dialect.name

    if dialect_name == "sqlite":
        result = await conn.execute(
            text("SELECT name FROM pragma_index_list(:table_name)"),
            {"table_name": table_name},
        )
        return {row[0] for row in result.fetchall()}

    result = await conn.execute(
        text("SELECT indexname FROM pg_indexes WHERE tablename = :table_name"),
        {"table_name": table_name},
    )
    return {row[0] for row in result.fetchall()}

async def _ensure_missing_indexes(
    conn: AsyncConnection,
    table_name: str,
    index_queries: dict[str, str],
    index_names: dict[str, str],
    existing_columns: set[str],
    auto_fix: bool,
) -> tuple[list[str], list[str], list[str]]:
    """إنشاء الفهارس المفقودة وتوثيق النتائج.

    Returns:
        tuple[list[str], list[str], list[str]]: (المفقودة، المثبتة، الأخطاء)
    """
    missing_indexes: list[str] = []
    fixed_indexes: list[str] = []
    errors: list[str] = []

    try:
        existing_indexes = await _get_existing_indexes(conn, table_name)
    except Exception as exc:
        return missing_indexes, fixed_indexes, [f"Error reading indexes for {table_name}: {exc}"]

    for key, index_query in index_queries.items():
        index_name = index_names.get(key) or _infer_index_name(index_query)

        if not index_name:
            errors.append(f"Unable to infer index name for {table_name}.{key}")
            continue

        if index_name in existing_indexes:
            continue

        if not auto_fix:
            missing_indexes.append(f"{table_name}.{index_name}")
            continue

        if key not in existing_columns:
            errors.append(
                f"Cannot create index {index_name} on {table_name} because column {key} is missing"
            )
            missing_indexes.append(f"{table_name}.{index_name}")
            continue

        try:
            await conn.execute(text(index_query))
            fixed_indexes.append(f"{table_name}.{index_name}")
            logger.info(f"✅ Created missing index: {table_name}.{index_name}")
        except Exception as exc:
            errors.append(f"Failed to create index {table_name}.{index_name}: {exc}")
            missing_indexes.append(f"{table_name}.{index_name}")

    return missing_indexes, fixed_indexes, errors

async def validate_and_fix_schema(auto_fix: bool = True) -> SchemaValidationResult:
    """
    التحقق من تطابق Schema وإصلاح المشاكل تلقائياً للأعمدة والفهارس.

    Args:
        auto_fix (bool): تفعيل محاولة الإصلاح التلقائي.

    Returns:
        SchemaValidationResult: تقرير بالنتيجة المكتوبة الأنواع.
    """
    results: SchemaValidationResult = {
        "status": "ok",
        "checked_tables": [],
        "missing_columns": [],
        "fixed_columns": [],
        "missing_indexes": [],
        "fixed_indexes": [],
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

                index_queries = schema_info.get("indexes", {})
                index_names = schema_info.get("index_names", {})

                if index_queries:
                    missing_idx, fixed_idx, index_errors = await _ensure_missing_indexes(
                        conn=conn,
                        table_name=table_name,
                        index_queries=index_queries,
                        index_names=index_names,
                        existing_columns=existing_columns,
                        auto_fix=auto_fix,
                    )

                    results["missing_indexes"].extend(missing_idx)
                    results["fixed_indexes"].extend(fixed_idx)
                    results["errors"].extend(index_errors)

            if results["fixed_columns"] or results["fixed_indexes"]:
                await conn.commit()

    except Exception as e:
        results["status"] = "error"
        results["errors"].append(f"Schema validation failed: {e}")
        logger.error(f"❌ Schema validation error: {e}")

    unresolved_columns = set(results["missing_columns"]) - set(results["fixed_columns"])
    unresolved_indexes = set(results["missing_indexes"]) - set(results["fixed_indexes"])

    if results["errors"]:
        results["status"] = "error"
    elif unresolved_columns or unresolved_indexes:
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
    elif results["fixed_columns"] or results["fixed_indexes"]:
        logger.warning(
            "⚠️ Schema auto-fixed: "
            f"columns={results['fixed_columns']}, indexes={results['fixed_indexes']}"
        )
    elif results["missing_columns"] or results["missing_indexes"]:
        logger.error(
            "❌ CRITICAL: Missing schema elements: "
            f"columns={results['missing_columns']}, indexes={results['missing_indexes']}"
        )

    if results["errors"]:
        for error in results["errors"]:
            logger.error(f"   Error: {error}")
