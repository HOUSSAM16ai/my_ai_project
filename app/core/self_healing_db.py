"""
Self Healing Db

هذا الملف جزء من مشروع CogniForge.
"""

from __future__ import annotations

import logging
import os
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import Enum
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine

logger = logging.getLogger(__name__)
_SAFE_IDENTIFIER = re.compile("^[a-zA-Z_][a-zA-Z0-9_]{0,62}$")
_ALLOWED_TABLES = frozenset({"admin_conversations", "admin_messages"})


def _validate_table_name(name: str) -> str:
    if name not in _ALLOWED_TABLES:
        raise ValueError(f"Table '{name}' is not in the allowed whitelist")
    if not _SAFE_IDENTIFIER.match(name):
        raise ValueError(f"Invalid table name: {name}")
    return name


def _validate_column_name(name: str) -> str:
    if not _SAFE_IDENTIFIER.match(name):
        raise ValueError(f"Invalid column name: {name}")
    return name


class ColumnType(Enum):
    INTEGER = "INTEGER"
    TEXT = "TEXT"
    VARCHAR = "VARCHAR(255)"
    BOOLEAN = "BOOLEAN"
    TIMESTAMP = "TIMESTAMP WITH TIME ZONE"
    JSON = "JSONB"
    FLOAT = "FLOAT"


@dataclass
class ColumnDefinition:
    name: str
    type: ColumnType
    nullable: bool = True
    default: str | None = None
    index: bool = False

    def __post_init__(self):
        _validate_column_name(self.name)


@dataclass
class TableSchema:
    name: str
    columns: list[ColumnDefinition] = field(default_factory=list)

    def __post_init__(self):
        _validate_table_name(self.name)


REQUIRED_SCHEMA: dict[str, TableSchema] = {
    "admin_conversations": TableSchema(
        name="admin_conversations",
        columns=[
            ColumnDefinition("id", ColumnType.INTEGER, nullable=False),
            ColumnDefinition("title", ColumnType.VARCHAR, nullable=False),
            ColumnDefinition("user_id", ColumnType.INTEGER, nullable=False, index=True),
            ColumnDefinition("conversation_type", ColumnType.VARCHAR, nullable=True),
            ColumnDefinition(
                "linked_mission_id", ColumnType.INTEGER, nullable=True, index=True
            ),
            ColumnDefinition("created_at", ColumnType.TIMESTAMP, nullable=True),
        ],
    ),
    "admin_messages": TableSchema(
        name="admin_messages",
        columns=[
            ColumnDefinition("id", ColumnType.INTEGER, nullable=False),
            ColumnDefinition(
                "conversation_id", ColumnType.INTEGER, nullable=False, index=True
            ),
            ColumnDefinition("role", ColumnType.TEXT, nullable=False),
            ColumnDefinition("content", ColumnType.TEXT, nullable=False),
            ColumnDefinition("created_at", ColumnType.TIMESTAMP, nullable=True),
        ],
    ),
}


class SQLGenerator:

    @staticmethod
    def add_column(table: str, column: ColumnDefinition) -> str:
        table = _validate_table_name(table)
        col_name = _validate_column_name(column.name)
        sql = f'ALTER TABLE "{table}" ADD COLUMN IF NOT EXISTS "{col_name}" {column.type.value}'
        if not column.nullable:
            sql += " NOT NULL"
        if column.default:
            sql += f" DEFAULT {column.default}"
        return sql

    @staticmethod
    def create_index(table: str, column: str) -> str:
        table = _validate_table_name(table)
        col_name = _validate_column_name(column)
        index_name = f"ix_{table}_{col_name}"
        return f'CREATE INDEX IF NOT EXISTS "{index_name}" ON "{table}"("{col_name}")'

    @staticmethod
    def get_columns_query(table: str) -> tuple[str, dict]:
        _validate_table_name(table)
        return (
            "SELECT column_name FROM information_schema.columns WHERE table_name = :table_name",
            {"table_name": table},
        )


@dataclass
class HealingOperation:
    table: str
    column: str
    operation: str
    sql: str
    success: bool = False
    error: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class HealingReport:
    started_at: datetime
    completed_at: datetime | None = None
    tables_checked: int = 0
    tables_healed: int = 0
    operations: list[HealingOperation] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    status: str = "pending"


class ExecutionStrategy(ABC):
    """Abstract base class for Unified Database Execution."""

    @abstractmethod
    async def execute(self, sql: str, params: dict | None = None) -> Any: ...

    @abstractmethod
    async def commit(self): ...

    @abstractmethod
    async def close(self): ...


class AsyncStrategy(ExecutionStrategy):

    def __init__(self, conn):
        self.conn = conn

    async def execute(self, sql: str, params: dict | None = None) -> Any:
        return await self.conn.execute(text(sql), params or {})

    async def commit(self):
        await self.conn.commit()

    async def close(self):
        pass


class SyncStrategy(ExecutionStrategy):

    def __init__(self, conn):
        self.conn = conn

    async def execute(self, sql: str, params: dict | None = None) -> Any:
        return self.conn.execute(text(sql), params or {})

    async def commit(self):
        self.conn.commit()

    async def close(self):
        pass


class SelfHealingEngine:
    """
    محرك الإصلاح الذاتي الخارق (Superhuman Self-Healing Engine).
    Unified Logic for both Sync and Async worlds.
    """

    def __init__(self, engine: Engine | AsyncEngine):
        self.engine = engine
        self._is_async = isinstance(engine, AsyncEngine)
        self._report: HealingReport | None = None

    async def _core_healing_logic(
        self, strategy: ExecutionStrategy, auto_fix: bool
    ) -> None:
        """The Unified Logic Core - One Brain for All Protocols."""
        for table_name, schema in REQUIRED_SCHEMA.items():
            self._report.tables_checked += 1
            try:
                query, params = SQLGenerator.get_columns_query(table_name)
                result = await strategy.execute(query, params)
                existing = {row[0] for row in result.fetchall()}
            except Exception as e:
                logger.warning(f"⚠️ Table {table_name} check failed: {e}")
                continue
            for column in schema.columns:
                if column.name not in existing:
                    logger.warning(f"🔍 Missing: {table_name}.{column.name}")
                    if auto_fix:
                        await self._apply_fix(strategy, table_name, column)
        if auto_fix and self._report.operations:
            await strategy.commit()

    async def _apply_fix(
        self, strategy: ExecutionStrategy, table: str, column: ColumnDefinition
    ):
        op = HealingOperation(
            table=table,
            column=column.name,
            operation="add_column",
            sql=SQLGenerator.add_column(table, column),
        )
        try:
            await strategy.execute(op.sql)
            op.success = True
            logger.info(f"✅ Added: {table}.{column.name}")
            if column.index:
                index_sql = SQLGenerator.create_index(table, column.name)
                await strategy.execute(index_sql)
                logger.info(f"✅ Indexed: {table}.{column.name}")
            self._report.tables_healed += 1
        except Exception as e:
            op.success = False
            op.error = str(e)
            self._report.errors.append(f"{table}.{column.name}: {e}")
            logger.error(f"❌ Failed: {table}.{column.name} - {e}")
        self._report.operations.append(op)

    async def heal_async(self, auto_fix: bool = True) -> HealingReport:
        self._report = HealingReport(started_at=datetime.now(UTC))
        logger.info("🧬 Superhuman Healer: Starting Async Diagnosis...")
        async with self.engine.connect() as conn:
            strategy = AsyncStrategy(conn)
            await self._core_healing_logic(strategy, auto_fix)
        self._finalize_report()
        return self._report

    def heal_sync(self, auto_fix: bool = True) -> HealingReport:
        from app.core.engine_factory import DatabaseURLSanitizer

        self._report = HealingReport(started_at=datetime.now(UTC))
        logger.info("🧬 Superhuman Healer: Starting Sync Diagnosis...")
        db_url = os.getenv("DATABASE_URL", "")
        db_url = DatabaseURLSanitizer.sanitize(db_url, for_async=False)
        if "asyncpg" in db_url:
            db_url = db_url.replace("postgresql+asyncpg", "postgresql")
        sync_engine = create_engine(db_url)
        with sync_engine.connect() as conn:
            strategy = SyncStrategy(conn)
            self._run_sync_logic(strategy, auto_fix)
        self._finalize_report()
        return self._report

    def _run_sync_logic(self, strategy: ExecutionStrategy, auto_fix: bool):
        """Sync version of the core logic using the unified strategy pattern."""
        for table_name, schema in REQUIRED_SCHEMA.items():
            self._report.tables_checked += 1
            try:
                query, params = SQLGenerator.get_columns_query(table_name)
                conn = strategy.conn
                result = conn.execute(text(query), params or {})
                existing = {row[0] for row in result.fetchall()}
            except Exception as e:
                logger.warning(f"⚠️ Table {table_name} check failed: {e}")
                continue
            for column in schema.columns:
                if column.name not in existing:
                    logger.warning(f"🔍 Missing: {table_name}.{column.name}")
                    if auto_fix:
                        self._apply_fix_sync(strategy, table_name, column)
        if auto_fix and self._report.operations:
            strategy.conn.commit()

    def _apply_fix_sync(
        self, strategy: ExecutionStrategy, table: str, column: ColumnDefinition
    ):
        op = HealingOperation(
            table=table,
            column=column.name,
            operation="add_column",
            sql=SQLGenerator.add_column(table, column),
        )
        try:
            strategy.conn.execute(text(op.sql))
            op.success = True
            logger.info(f"✅ Added: {table}.{column.name}")
            if column.index:
                index_sql = SQLGenerator.create_index(table, column.name)
                strategy.conn.execute(text(index_sql))
                logger.info(f"✅ Indexed: {table}.{column.name}")
            self._report.tables_healed += 1
        except Exception as e:
            op.success = False
            op.error = str(e)
            self._report.errors.append(f"{table}.{column.name}: {e}")
            logger.error(f"❌ Failed: {table}.{column.name} - {e}")
        self._report.operations.append(op)

    def _finalize_report(self):
        self._report.completed_at = datetime.now(UTC)
        self._report.status = "success" if not self._report.errors else "partial"
        self._log_report()

    def _log_report(self):
        if not self._report:
            return
        logger.info("=" * 50)
        logger.info("🧬 SUPERHUMAN SELF-HEALING REPORT")
        logger.info(f"   Status: {self._report.status}")
        logger.info(f"   Checked: {self._report.tables_checked} tables")
        logger.info(f"   Healed: {self._report.tables_healed} tables")
        logger.info("=" * 50)

    def heal_api_error(self, error: Exception, context: dict) -> dict:
        """
        Simulates AI-driven API error healing.
        Analyzes the exception and returns a 'healed' response or suggestion.
        """
        error_str = str(error)
        logger.warning(f"🩹 Healing API Error: {error_str} | Context: {context}")
        if "404" in error_str:
            return {
                "healed": True,
                "action": "redirect",
                "suggestion": "Resource not found. Suggest checking parent ID.",
            }
        elif "500" in error_str:
            return {
                "healed": False,
                "action": "escalate",
                "suggestion": "Critical internal error. Escalating to Overmind.",
            }
        return {
            "healed": False,
            "action": "log_only",
            "suggestion": "No specific fix found.",
        }


_healing_engine: SelfHealingEngine | None = None


def get_healing_engine() -> SelfHealingEngine:
    global _healing_engine
    if _healing_engine is None:
        from app.core.database import engine

        _healing_engine = SelfHealingEngine(engine)
    return _healing_engine


def run_self_healing_sync(auto_fix: bool = True) -> HealingReport:
    engine = get_healing_engine()
    return engine.heal_sync(auto_fix=auto_fix)
