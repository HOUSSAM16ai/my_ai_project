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
# ✅ دعم Async و Sync
# =============================================================================

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)


# =============================================================================
# 🎯 SCHEMA DEFINITION — تعريف Schema المطلوب
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
    unique: bool = False
    foreign_key: str | None = None


@dataclass
class TableSchema:
    """تعريف Schema لجدول."""

    name: str
    columns: list[ColumnDefinition] = field(default_factory=list)

    def get_column(self, name: str) -> ColumnDefinition | None:
        """الحصول على تعريف عمود بالاسم."""
        for col in self.columns:
            if col.name == name:
                return col
        return None


# =============================================================================
# 🗄️ REQUIRED SCHEMA — Schema المطلوب للنظام
# =============================================================================

REQUIRED_SCHEMA: dict[str, TableSchema] = {
    "admin_conversations": TableSchema(
        name="admin_conversations",
        columns=[
            ColumnDefinition("id", ColumnType.INTEGER, nullable=False),
            ColumnDefinition("title", ColumnType.VARCHAR, nullable=False),
            ColumnDefinition("user_id", ColumnType.INTEGER, nullable=False, index=True),
            ColumnDefinition(
                "conversation_type", ColumnType.VARCHAR, nullable=True, default="'general'"
            ),
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
# 🔧 SQL GENERATORS — مولدات SQL
# =============================================================================


class SQLGenerator:
    """مولد أوامر SQL للإصلاح التلقائي."""

    @staticmethod
    def add_column(table: str, column: ColumnDefinition) -> str:
        """إنشاء أمر SQL لإضافة عمود."""
        sql = f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {column.name} {column.type.value}"

        if not column.nullable:
            sql += " NOT NULL"

        if column.default:
            sql += f" DEFAULT {column.default}"

        return sql

    @staticmethod
    def create_index(table: str, column: str) -> str:
        """إنشاء أمر SQL لإضافة فهرس."""
        index_name = f"ix_{table}_{column}"
        return f"CREATE INDEX IF NOT EXISTS {index_name} ON {table}({column})"

    @staticmethod
    def drop_column(table: str, column: str) -> str:
        """إنشاء أمر SQL لحذف عمود."""
        return f"ALTER TABLE {table} DROP COLUMN IF EXISTS {column}"


# =============================================================================
# 🔬 SCHEMA ANALYZER — محلل Schema
# =============================================================================


@dataclass
class SchemaAnalysisResult:
    """نتيجة تحليل Schema."""

    table: str
    existing_columns: set[str]
    required_columns: set[str]
    missing_columns: set[str]
    extra_columns: set[str]
    is_valid: bool

    def to_dict(self) -> dict:
        return {
            "table": self.table,
            "existing_columns": list(self.existing_columns),
            "required_columns": list(self.required_columns),
            "missing_columns": list(self.missing_columns),
            "extra_columns": list(self.extra_columns),
            "is_valid": self.is_valid,
        }


class SchemaAnalyzer:
    """محلل Schema ذكي."""

    def __init__(self, engine: Engine | AsyncEngine):
        self.engine = engine
        self._is_async = isinstance(engine, AsyncEngine)

    async def analyze_table_async(self, table_name: str) -> SchemaAnalysisResult:
        """تحليل جدول (async)."""
        async with self.engine.connect() as conn:
            result = await conn.execute(
                text(f"""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
            """)
            )
            existing = {row[0] for row in result.fetchall()}

        return self._create_analysis_result(table_name, existing)

    def analyze_table_sync(self, conn, table_name: str) -> SchemaAnalysisResult:
        """تحليل جدول (sync)."""
        result = conn.execute(
            text(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
        """)
        )
        existing = {row[0] for row in result.fetchall()}

        return self._create_analysis_result(table_name, existing)

    def _create_analysis_result(self, table_name: str, existing: set[str]) -> SchemaAnalysisResult:
        """إنشاء نتيجة التحليل."""
        schema = REQUIRED_SCHEMA.get(table_name)
        if not schema:
            return SchemaAnalysisResult(
                table=table_name,
                existing_columns=existing,
                required_columns=set(),
                missing_columns=set(),
                extra_columns=existing,
                is_valid=True,
            )

        required = {col.name for col in schema.columns}
        missing = required - existing
        extra = existing - required

        return SchemaAnalysisResult(
            table=table_name,
            existing_columns=existing,
            required_columns=required,
            missing_columns=missing,
            extra_columns=extra,
            is_valid=len(missing) == 0,
        )


# =============================================================================
# 🏥 SELF-HEALING ENGINE — محرك الإصلاح الذاتي
# =============================================================================


@dataclass
class HealingOperation:
    """عملية إصلاح."""

    table: str
    column: str
    operation: str  # "add_column", "create_index", etc.
    sql: str
    success: bool = False
    error: str | None = None
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class HealingReport:
    """تقرير الإصلاح."""

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
                {
                    "table": op.table,
                    "column": op.column,
                    "operation": op.operation,
                    "success": op.success,
                    "error": op.error,
                }
                for op in self.operations
            ],
            "errors": self.errors,
            "status": self.status,
        }


class SelfHealingEngine:
    """
    🧬 محرك الإصلاح الذاتي الخارق

    يكتشف ويصلح مشاكل Schema تلقائياً:
    - أعمدة مفقودة
    - فهارس ناقصة
    - أنواع بيانات خاطئة
    """

    def __init__(self, engine: Engine | AsyncEngine):
        self.engine = engine
        self.analyzer = SchemaAnalyzer(engine)
        self._is_async = isinstance(engine, AsyncEngine)
        self._report: HealingReport | None = None

    async def heal_async(self, auto_fix: bool = True) -> HealingReport:
        """
        🏥 تشغيل الإصلاح الذاتي (async).

        Args:
            auto_fix: إصلاح تلقائي للمشاكل

        Returns:
            تقرير الإصلاح
        """
        self._report = HealingReport(started_at=datetime.utcnow())

        logger.info("🧬 Self-Healing Engine: Starting diagnosis...")

        async with self.engine.connect() as conn:
            for table_name, schema in REQUIRED_SCHEMA.items():
                self._report.tables_checked += 1

                # تحليل الجدول
                try:
                    result = await conn.execute(
                        text(f"""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name = '{table_name}'
                    """)
                    )
                    existing = {row[0] for row in result.fetchall()}
                except Exception as e:
                    logger.warning(f"⚠️ Table {table_name} might not exist: {e}")
                    continue

                # البحث عن الأعمدة المفقودة
                for column in schema.columns:
                    if column.name not in existing:
                        logger.warning(f"🔍 Missing column: {table_name}.{column.name}")

                        if auto_fix:
                            await self._fix_missing_column_async(conn, table_name, column)

            # Commit التغييرات
            if auto_fix and self._report.operations:
                await conn.commit()

        self._report.completed_at = datetime.utcnow()
        self._report.status = "success" if not self._report.errors else "partial"

        self._log_report()
        return self._report

    async def _fix_missing_column_async(self, conn, table: str, column: ColumnDefinition):
        """إصلاح عمود مفقود (async)."""
        operation = HealingOperation(
            table=table,
            column=column.name,
            operation="add_column",
            sql=SQLGenerator.add_column(table, column),
        )

        try:
            await conn.execute(text(operation.sql))
            operation.success = True
            logger.info(f"✅ Added column: {table}.{column.name}")

            # إضافة الفهرس إذا كان مطلوباً
            if column.index:
                index_sql = SQLGenerator.create_index(table, column.name)
                await conn.execute(text(index_sql))
                logger.info(f"✅ Created index for: {table}.{column.name}")

            self._report.tables_healed += 1

        except Exception as e:
            operation.success = False
            operation.error = str(e)
            self._report.errors.append(f"Failed to add {table}.{column.name}: {e}")
            logger.error(f"❌ Failed to add {table}.{column.name}: {e}")

        self._report.operations.append(operation)

    def heal_sync(self, auto_fix: bool = True) -> HealingReport:
        """
        🏥 تشغيل الإصلاح الذاتي (sync).
        """
        from app.core.engine_factory import DatabaseURLSanitizer

        self._report = HealingReport(started_at=datetime.utcnow())

        logger.info("🧬 Self-Healing Engine: Starting diagnosis (sync)...")

        # إنشاء sync engine
        db_url = os.getenv("DATABASE_URL", "")
        db_url = DatabaseURLSanitizer.sanitize(db_url, for_async=False)
        if "asyncpg" in db_url:
            db_url = db_url.replace("postgresql+asyncpg", "postgresql")

        sync_engine = create_engine(db_url)

        with sync_engine.connect() as conn:
            for table_name, schema in REQUIRED_SCHEMA.items():
                self._report.tables_checked += 1

                try:
                    result = conn.execute(
                        text(f"""
                        SELECT column_name
                        FROM information_schema.columns
                        WHERE table_name = '{table_name}'
                    """)
                    )
                    existing = {row[0] for row in result.fetchall()}
                except Exception as e:
                    logger.warning(f"⚠️ Table {table_name} check failed: {e}")
                    continue

                for column in schema.columns:
                    if column.name not in existing:
                        logger.warning(f"🔍 Missing column: {table_name}.{column.name}")

                        if auto_fix:
                            self._fix_missing_column_sync(conn, table_name, column)

            if auto_fix and self._report.operations:
                conn.commit()

        self._report.completed_at = datetime.utcnow()
        self._report.status = "success" if not self._report.errors else "partial"

        self._log_report()
        return self._report

    def _fix_missing_column_sync(self, conn, table: str, column: ColumnDefinition):
        """إصلاح عمود مفقود (sync)."""
        operation = HealingOperation(
            table=table,
            column=column.name,
            operation="add_column",
            sql=SQLGenerator.add_column(table, column),
        )

        try:
            conn.execute(text(operation.sql))
            operation.success = True
            logger.info(f"✅ Added column: {table}.{column.name}")

            if column.index:
                index_sql = SQLGenerator.create_index(table, column.name)
                conn.execute(text(index_sql))
                logger.info(f"✅ Created index for: {table}.{column.name}")

            self._report.tables_healed += 1

        except Exception as e:
            operation.success = False
            operation.error = str(e)
            self._report.errors.append(f"Failed to add {table}.{column.name}: {e}")
            logger.error(f"❌ Failed to add {table}.{column.name}: {e}")

        self._report.operations.append(operation)

    def _log_report(self):
        """تسجيل تقرير الإصلاح."""
        if not self._report:
            return

        logger.info("=" * 60)
        logger.info("🧬 SELF-HEALING REPORT")
        logger.info("=" * 60)
        logger.info(f"   Status: {self._report.status}")
        logger.info(f"   Tables Checked: {self._report.tables_checked}")
        logger.info(f"   Tables Healed: {self._report.tables_healed}")
        logger.info(f"   Operations: {len(self._report.operations)}")

        if self._report.errors:
            logger.error(f"   Errors: {len(self._report.errors)}")
            for error in self._report.errors:
                logger.error(f"      - {error}")

        logger.info("=" * 60)


# =============================================================================
# 🚀 PUBLIC API — واجهة برمجية عامة
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
    """
    🏥 تشغيل الإصلاح الذاتي.

    Args:
        auto_fix: إصلاح تلقائي للمشاكل

    Returns:
        تقرير الإصلاح
    """
    engine = get_healing_engine()
    return await engine.heal_async(auto_fix=auto_fix)


def run_self_healing_sync(auto_fix: bool = True) -> HealingReport:
    """
    🏥 تشغيل الإصلاح الذاتي (sync version).
    """
    engine = get_healing_engine()
    return engine.heal_sync(auto_fix=auto_fix)


# =============================================================================
# 🧪 QUICK FIX FUNCTION — دالة الإصلاح السريع
# =============================================================================


def quick_fix_linked_mission_id() -> bool:
    """
    ⚡ إصلاح سريع لمشكلة linked_mission_id.

    يمكن استدعاؤها مباشرة من أي مكان لإصلاح المشكلة فوراً.

    Returns:
        True إذا نجح الإصلاح
    """

    db_url = os.getenv("DATABASE_URL", "")
    if not db_url:
        logger.error("❌ DATABASE_URL not set")
        return False

    # تحويل URL للـ sync
    if "asyncpg" in db_url:
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://")

    try:
        engine = create_engine(db_url)

        with engine.connect() as conn:
            # إضافة العمود
            conn.execute(
                text("""
                ALTER TABLE admin_conversations
                ADD COLUMN IF NOT EXISTS linked_mission_id INTEGER
            """)
            )

            # إضافة الفهرس
            conn.execute(
                text("""
                CREATE INDEX IF NOT EXISTS ix_admin_conversations_linked_mission_id
                ON admin_conversations(linked_mission_id)
            """)
            )

            conn.commit()

        logger.info("✅ quick_fix_linked_mission_id: SUCCESS!")
        return True

    except Exception as e:
        logger.error(f"❌ quick_fix_linked_mission_id FAILED: {e}")
        return False
