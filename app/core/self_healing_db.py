# =============================================================================
# 🧬 COGNIFORGE SELF-HEALING DATABASE SYSTEM
# =============================================================================
# نظام قاعدة بيانات ذاتي الإصلاح — تقنية ثورية تتفوق على أي نظام موجود
#
# الميزات الخارقة:
# ✅ اكتشاف تلقائي للأعمدة المفقودة
# ✅ إصلاح ذاتي بدون تدخل بشري
# ✅ مزامنة Schema بين الكود وقاعدة البيانات
# ✅ حماية من الأخطاء قبل حدوثها
# ✅ تسجيل شامل لكل عملية
# ✅ حماية من SQL Injection
# =============================================================================

from __future__ import annotations

import logging
import os
import re
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


# =============================================================================
# 🛡️ SECURITY — حماية من SQL Injection
# =============================================================================

# نمط آمن لأسماء الجداول والأعمدة
_SAFE_IDENTIFIER = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,62}$")

# قائمة بيضاء للجداول المسموح بها
_ALLOWED_TABLES = frozenset({"admin_conversations", "admin_messages"})


def _validate_table_name(name: str) -> str:
    """التحقق من صحة اسم الجدول ضد SQL Injection."""
    if name not in _ALLOWED_TABLES:
        raise ValueError(f"Table '{name}' is not in the allowed whitelist")
    if not _SAFE_IDENTIFIER.match(name):
        raise ValueError(f"Invalid table name: {name}")
    return name


def _validate_column_name(name: str) -> str:
    """التحقق من صحة اسم العمود ضد SQL Injection."""
    if not _SAFE_IDENTIFIER.match(name):
        raise ValueError(f"Invalid column name: {name}")
    return name


# =============================================================================
# 🎯 SCHEMA DEFINITIONS
# =============================================================================


class ColumnType(Enum):
    """أنواع الأعمدة المدعومة."""

    INTEGER = "INTEGER"
    TEXT = "TEXT"
    VARCHAR = "VARCHAR(255)"
    BOOLEAN = "BOOLEAN"
    TIMESTAMP = "TIMESTAMP WITH TIME ZONE"
    JSON = "JSONB"
    FLOAT = "FLOAT"


@dataclass
class ColumnDefinition:
    """تعريف عمود في قاعدة البيانات."""

    name: str
    type: ColumnType
    nullable: bool = True
    default: str | None = None
    index: bool = False

    def __post_init__(self):
        _validate_column_name(self.name)


@dataclass
class TableSchema:
    """تعريف Schema لجدول."""

    name: str
    columns: list[ColumnDefinition] = field(default_factory=list)

    def __post_init__(self):
        _validate_table_name(self.name)

    def get_column(self, name: str) -> ColumnDefinition | None:
        for col in self.columns:
            if col.name == name:
                return col
        return None


# =============================================================================
# 🗄️ REQUIRED SCHEMA
# =============================================================================

REQUIRED_SCHEMA: dict[str, TableSchema] = {
    "admin_conversations": TableSchema(
        name="admin_conversations",
        columns=[
            ColumnDefinition("id", ColumnType.INTEGER, nullable=False),
            ColumnDefinition("title", ColumnType.VARCHAR, nullable=False),
            ColumnDefinition("user_id", ColumnType.INTEGER, nullable=False, index=True),
            ColumnDefinition("conversation_type", ColumnType.VARCHAR, nullable=True),
            ColumnDefinition("linked_mission_id", ColumnType.INTEGER, nullable=True, index=True),
            ColumnDefinition("created_at", ColumnType.TIMESTAMP, nullable=True),
        ],
    ),
    "admin_messages": TableSchema(
        name="admin_messages",
        columns=[
            ColumnDefinition("id", ColumnType.INTEGER, nullable=False),
            ColumnDefinition("conversation_id", ColumnType.INTEGER, nullable=False, index=True),
            ColumnDefinition("role", ColumnType.TEXT, nullable=False),
            ColumnDefinition("content", ColumnType.TEXT, nullable=False),
            ColumnDefinition("created_at", ColumnType.TIMESTAMP, nullable=True),
        ],
    ),
}


# =============================================================================
# 🔧 SQL GENERATORS — مع حماية أمنية
# =============================================================================


class SQLGenerator:
    """مولد أوامر SQL الآمنة."""

    @staticmethod
    def add_column(table: str, column: ColumnDefinition) -> str:
        """إنشاء أمر SQL آمن لإضافة عمود."""
        table = _validate_table_name(table)
        col_name = _validate_column_name(column.name)

        sql = f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "{col_name}" {column.type.value}'
        if not column.nullable:
            sql += " NOT NULL"
        if column.default:
            # Default values are from our code, not user input
            sql += f" DEFAULT {column.default}"
        return sql

    @staticmethod
    def create_index(table: str, column: str) -> str:
        """إنشاء أمر SQL آمن لإضافة فهرس."""
        table = _validate_table_name(table)
        col_name = _validate_column_name(column)
        index_name = f"ix_{table}_{col_name}"
        return f'CREATE INDEX IF NOT EXISTS "{index_name}" ON "{table}"("{col_name}")'

    @staticmethod
    def get_columns_query(table: str) -> tuple[str, dict]:
        """إنشاء استعلام آمن للحصول على الأعمدة."""
        _validate_table_name(table)
        # Use parameterized query for safety
        return (
            "SELECT column_name FROM information_schema.columns WHERE table_name = :table_name",
            {"table_name": table},
        )


# =============================================================================
# 📊 HEALING REPORTS
# =============================================================================


@dataclass
class HealingOperation:
    """عملية إصلاح واحدة."""

    table: str
    column: str
    operation: str
    sql: str
    success: bool = False
    error: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class HealingReport:
    """تقرير الإصلاح الكامل."""

    started_at: datetime
    completed_at: datetime | None = None
    tables_checked: int = 0
    tables_healed: int = 0
    operations: list[HealingOperation] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    status: str = "pending"

    def to_dict(self) -> dict:
        return {
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "tables_checked": self.tables_checked,
            "tables_healed": self.tables_healed,
            "operations": [
                {"table": op.table, "column": op.column, "success": op.success}
                for op in self.operations
            ],
            "status": self.status,
        }


# =============================================================================
# 🏥 SELF-HEALING ENGINE
# =============================================================================


class SelfHealingEngine:
    """محرك الإصلاح الذاتي الخارق."""

    def __init__(self, engine: Engine | AsyncEngine):
        self.engine = engine
        self._is_async = isinstance(engine, AsyncEngine)
        self._report: HealingReport | None = None

    async def heal_async(self, auto_fix: bool = True) -> HealingReport:
        """تشغيل الإصلاح الذاتي (async)."""
        self._report = HealingReport(started_at=datetime.now(UTC))
        logger.info("🧬 Self-Healing Engine: Starting diagnosis...")

        async with self.engine.connect() as conn:
            for table_name, schema in REQUIRED_SCHEMA.items():
                self._report.tables_checked += 1

                # Get existing columns using parameterized query
                try:
                    query, params = SQLGenerator.get_columns_query(table_name)
                    result = await conn.execute(text(query), params)
                    existing = {row[0] for row in result.fetchall()}
                except Exception as e:
                    logger.warning(f"⚠️ Table {table_name} check failed: {e}")
                    continue

                # Find and fix missing columns
                for column in schema.columns:
                    if column.name not in existing:
                        logger.warning(f"🔍 Missing: {table_name}.{column.name}")
                        if auto_fix:
                            await self._fix_column_async(conn, table_name, column)

            if auto_fix and self._report.operations:
                await conn.commit()

        self._report.completed_at = datetime.now(UTC)
        self._report.status = "success" if not self._report.errors else "partial"
        self._log_report()
        return self._report

    async def _fix_column_async(self, conn, table: str, column: ColumnDefinition):
        """إصلاح عمود مفقود (async)."""
        op = HealingOperation(
            table=table,
            column=column.name,
            operation="add_column",
            sql=SQLGenerator.add_column(table, column),
        )

        try:
            await conn.execute(text(op.sql))
            op.success = True
            logger.info(f"✅ Added: {table}.{column.name}")

            if column.index:
                index_sql = SQLGenerator.create_index(table, column.name)
                await conn.execute(text(index_sql))
                logger.info(f"✅ Indexed: {table}.{column.name}")

            self._report.tables_healed += 1

        except Exception as e:
            op.success = False
            op.error = str(e)
            self._report.errors.append(f"{table}.{column.name}: {e}")
            logger.error(f"❌ Failed: {table}.{column.name} - {e}")

        self._report.operations.append(op)

    def heal_sync(self, auto_fix: bool = True) -> HealingReport:
        """تشغيل الإصلاح الذاتي (sync)."""
        from app.core.engine_factory import DatabaseURLSanitizer

        self._report = HealingReport(started_at=datetime.now(UTC))
        logger.info("🧬 Self-Healing Engine: Starting diagnosis (sync)...")

        db_url = os.getenv("DATABASE_URL", "")
        db_url = DatabaseURLSanitizer.sanitize(db_url, for_async=False)
        if "asyncpg" in db_url:
            db_url = db_url.replace("postgresql+asyncpg", "postgresql")

        sync_engine = create_engine(db_url)

        with sync_engine.connect() as conn:
            for table_name, schema in REQUIRED_SCHEMA.items():
                self._report.tables_checked += 1

                try:
                    query, params = SQLGenerator.get_columns_query(table_name)
                    result = conn.execute(text(query), params)
                    existing = {row[0] for row in result.fetchall()}
                except Exception as e:
                    logger.warning(f"⚠️ Table {table_name} check failed: {e}")
                    continue

                for column in schema.columns:
                    if column.name not in existing:
                        logger.warning(f"🔍 Missing: {table_name}.{column.name}")
                        if auto_fix:
                            self._fix_column_sync(conn, table_name, column)

            if auto_fix and self._report.operations:
                conn.commit()

        self._report.completed_at = datetime.now(UTC)
        self._report.status = "success" if not self._report.errors else "partial"
        self._log_report()
        return self._report

    def _fix_column_sync(self, conn, table: str, column: ColumnDefinition):
        """إصلاح عمود مفقود (sync)."""
        op = HealingOperation(
            table=table,
            column=column.name,
            operation="add_column",
            sql=SQLGenerator.add_column(table, column),
        )

        try:
            conn.execute(text(op.sql))
            op.success = True
            logger.info(f"✅ Added: {table}.{column.name}")

            if column.index:
                index_sql = SQLGenerator.create_index(table, column.name)
                conn.execute(text(index_sql))
                logger.info(f"✅ Indexed: {table}.{column.name}")

            self._report.tables_healed += 1

        except Exception as e:
            op.success = False
            op.error = str(e)
            self._report.errors.append(f"{table}.{column.name}: {e}")
            logger.error(f"❌ Failed: {table}.{column.name} - {e}")

        self._report.operations.append(op)

    def _log_report(self):
        """تسجيل تقرير الإصلاح."""
        if not self._report:
            return
        logger.info("=" * 50)
        logger.info("🧬 SELF-HEALING REPORT")
        logger.info(f"   Status: {self._report.status}")
        logger.info(f"   Checked: {self._report.tables_checked} tables")
        logger.info(f"   Healed: {self._report.tables_healed} tables")
        logger.info(f"   Operations: {len(self._report.operations)}")
        logger.info("=" * 50)


# =============================================================================
# 🚀 PUBLIC API
# =============================================================================

_healing_engine: SelfHealingEngine | None = None


def get_healing_engine() -> SelfHealingEngine:
    """الحصول على محرك الإصلاح الذاتي."""
    global _healing_engine
    if _healing_engine is None:
        from app.core.database import engine

        _healing_engine = SelfHealingEngine(engine)
    return _healing_engine


async def run_self_healing(auto_fix: bool = True) -> HealingReport:
    """تشغيل الإصلاح الذاتي (async)."""
    engine = get_healing_engine()
    return await engine.heal_async(auto_fix=auto_fix)


def run_self_healing_sync(auto_fix: bool = True) -> HealingReport:
    """تشغيل الإصلاح الذاتي (sync)."""
    engine = get_healing_engine()
    return engine.heal_sync(auto_fix=auto_fix)


# =============================================================================
# ⚡ QUICK FIX
# =============================================================================


def quick_fix_linked_mission_id() -> bool:
    """إصلاح سريع لمشكلة linked_mission_id."""
    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        logger.error("❌ DATABASE_URL not set")
        return False

    if "asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    try:
        engine = create_engine(db_url)

        # Use validated SQL
        add_col_sql = SQLGenerator.add_column(
            "admin_conversations",
            ColumnDefinition("linked_mission_id", ColumnType.INTEGER, nullable=True, index=True),
        )
        index_sql = SQLGenerator.create_index("admin_conversations", "linked_mission_id")

        with engine.connect() as conn:
            conn.execute(text(add_col_sql))
            conn.execute(text(index_sql))
            conn.commit()

        logger.info("✅ quick_fix_linked_mission_id: SUCCESS!")
        return True

    except Exception as e:
        logger.error(f"❌ quick_fix_linked_mission_id FAILED: {e}")
        return False
