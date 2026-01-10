"""Database Schema Validator.

Responsible for validating and auto-repairing database schema at startup.
Separated from `database.py` to adhere to SRP.

Standards:
- CS50 2025: Arabic Documentation.
- Fail-Fast: Detect errors early.
- Dialect Agnostic: Supports PostgreSQL and SQLite.
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
# 🛡️ Schema Configuration
# =============================================================================

# Whitelist for security
_ALLOWED_TABLES: Final[frozenset[str]] = frozenset(
    {
        "admin_conversations",
        "audit_log",
        "customer_conversations",
        "customer_messages",
        "permissions",
        "refresh_tokens",
        "role_permissions",
        "roles",
        "user_roles",
        "users",
        "missions",
        "mission_plans",
        "tasks",
        "mission_events",
        "prompt_templates",
        "generated_prompts",
    }
)

class TableSchemaConfig(TypedDict):
    """Schema definition for a table."""

    columns: list[str]
    auto_fix: dict[str, str]
    indexes: dict[str, str]
    index_names: NotRequired[dict[str, str]]
    create_table: NotRequired[str]


class SchemaValidationResult(TypedDict):
    """Validation result with fix details."""

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
            "linked_mission_id": 'ALTER TABLE "admin_conversations" ADD COLUMN "linked_mission_id" INTEGER'
        },
        "indexes": {
            "linked_mission_id": 'CREATE INDEX IF NOT EXISTS "ix_admin_conversations_linked_mission_id" ON "admin_conversations"("linked_mission_id")'
        },
        "index_names": {"linked_mission_id": "ix_admin_conversations_linked_mission_id"},
        "create_table": (
            "CREATE TABLE IF NOT EXISTS \"admin_conversations\"("
            '"id" SERIAL PRIMARY KEY,'
            '"title" VARCHAR(500) NOT NULL,'
            '"user_id" INTEGER NOT NULL REFERENCES "users"("id") ON DELETE CASCADE,'
            '"conversation_type" VARCHAR(50) DEFAULT \'general\','
            '"linked_mission_id" INTEGER,'
            '"created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()'
            ")"
        ),
    },
    "customer_conversations": {
        "columns": [
            "id",
            "title",
            "user_id",
            "created_at",
        ],
        "auto_fix": {},
        "indexes": {
            "user_id": 'CREATE INDEX IF NOT EXISTS "ix_customer_conversations_user_id" ON "customer_conversations"("user_id")'
        },
        "index_names": {"user_id": "ix_customer_conversations_user_id"},
        "create_table": (
            "CREATE TABLE IF NOT EXISTS \"customer_conversations\"("
            '"id" SERIAL PRIMARY KEY,'
            '"title" VARCHAR(500) NOT NULL,'
            '"user_id" INTEGER NOT NULL REFERENCES "users"("id") ON DELETE CASCADE,'
            '"created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()'
            ")"
        ),
    },
    "customer_messages": {
        "columns": [
            "id",
            "conversation_id",
            "role",
            "content",
            "policy_flags",
            "created_at",
        ],
        "auto_fix": {},
        "indexes": {
            "conversation_id": 'CREATE INDEX IF NOT EXISTS "ix_customer_messages_conversation_id" ON "customer_messages"("conversation_id")'
        },
        "index_names": {"conversation_id": "ix_customer_messages_conversation_id"},
        "create_table": (
            "CREATE TABLE IF NOT EXISTS \"customer_messages\"("
            '"id" SERIAL PRIMARY KEY,'
            '"conversation_id" INTEGER NOT NULL REFERENCES "customer_conversations"("id") ON DELETE CASCADE,'
            '"role" VARCHAR(50) NOT NULL,'
            '"content" TEXT NOT NULL,'
            '"policy_flags" TEXT,'
            '"created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()'
            ")"
        ),
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
            "external_id": 'ALTER TABLE "users" ADD COLUMN "external_id" VARCHAR(36)',
            "is_active": 'ALTER TABLE "users" ADD COLUMN "is_active" BOOLEAN NOT NULL DEFAULT TRUE',
            "status": 'ALTER TABLE "users" ADD COLUMN "status" VARCHAR(50) NOT NULL DEFAULT \'active\''
        },
        "indexes": {
            "external_id": 'CREATE UNIQUE INDEX IF NOT EXISTS "ix_users_external_id" ON "users"("external_id")'
        },
        "index_names": {"external_id": "ix_users_external_id"},
        "create_table": (
            "CREATE TABLE IF NOT EXISTS \"users\"("
            '"id" SERIAL PRIMARY KEY,'
            '"external_id" VARCHAR(36) UNIQUE,'
            '"full_name" VARCHAR(150) NOT NULL,'
            '"email" VARCHAR(150) NOT NULL UNIQUE,'
            '"password_hash" VARCHAR(256),'
            '"is_admin" BOOLEAN DEFAULT FALSE,'
            '"is_active" BOOLEAN DEFAULT TRUE,'
            '"status" VARCHAR(50) DEFAULT \'active\','
            '"created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),'
            '"updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()'
            ")"
        ),
    },
    "roles": {
        "columns": [
            "id",
            "name",
            "description",
            "created_at",
            "updated_at",
        ],
        "auto_fix": {},
        "indexes": {
            "name": 'CREATE UNIQUE INDEX IF NOT EXISTS "ix_roles_name" ON "roles"("name")',
        },
        "index_names": {"name": "ix_roles_name"},
        "create_table": (
            "CREATE TABLE IF NOT EXISTS \"roles\"("
            '"id" SERIAL PRIMARY KEY,'
            '"name" VARCHAR(100) NOT NULL UNIQUE,'
            '"description" VARCHAR(255),'
            '"created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),'
            '"updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()'
            ")"
        ),
    },
    "permissions": {
        "columns": [
            "id",
            "name",
            "description",
            "created_at",
            "updated_at",
        ],
        "auto_fix": {},
        "indexes": {
            "name": 'CREATE UNIQUE INDEX IF NOT EXISTS "ix_permissions_name" ON "permissions"("name")',
        },
        "index_names": {"name": "ix_permissions_name"},
        "create_table": (
            "CREATE TABLE IF NOT EXISTS \"permissions\"("
            '"id" SERIAL PRIMARY KEY,'
            '"name" VARCHAR(100) NOT NULL UNIQUE,'
            '"description" VARCHAR(255),'
            '"created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),'
            '"updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()'
            ")"
        ),
    },
    "user_roles": {
        "columns": ["user_id", "role_id", "created_at"],
        "auto_fix": {},
        "indexes": {
            "user_id": 'CREATE INDEX IF NOT EXISTS "ix_user_roles_user_id" ON "user_roles"("user_id")',
            "role_id": 'CREATE INDEX IF NOT EXISTS "ix_user_roles_role_id" ON "user_roles"("role_id")',
        },
        "index_names": {
            "user_id": "ix_user_roles_user_id",
            "role_id": "ix_user_roles_role_id",
        },
        "create_table": (
            "CREATE TABLE IF NOT EXISTS \"user_roles\"("
            '"user_id" INTEGER NOT NULL REFERENCES "users"("id") ON DELETE CASCADE,'
            '"role_id" INTEGER NOT NULL REFERENCES "roles"("id") ON DELETE CASCADE,'
            '"created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),'
            'PRIMARY KEY ("user_id", "role_id")'
            ")"
        ),
    },
    "role_permissions": {
        "columns": ["role_id", "permission_id", "created_at"],
        "auto_fix": {},
        "indexes": {
            "role_id": 'CREATE INDEX IF NOT EXISTS "ix_role_permissions_role_id" ON "role_permissions"("role_id")',
            "permission_id": 'CREATE INDEX IF NOT EXISTS "ix_role_permissions_permission_id" ON "role_permissions"("permission_id")',
        },
        "index_names": {
            "role_id": "ix_role_permissions_role_id",
            "permission_id": "ix_role_permissions_permission_id",
        },
        "create_table": (
            "CREATE TABLE IF NOT EXISTS \"role_permissions\"("
            '"role_id" INTEGER NOT NULL REFERENCES "roles"("id") ON DELETE CASCADE,'
            '"permission_id" INTEGER NOT NULL REFERENCES "permissions"("id") ON DELETE CASCADE,'
            '"created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),'
            'PRIMARY KEY ("role_id", "permission_id")'
            ")"
        ),
    },
    "refresh_tokens": {
        "columns": [
            "id",
            "token_id",
            "user_id",
            "hashed_token",
            "expires_at",
            "revoked_at",
            "created_at",
        ],
        "auto_fix": {},
        "indexes": {
            "user_id": 'CREATE INDEX IF NOT EXISTS "ix_refresh_tokens_user_id" ON "refresh_tokens"("user_id")',
            "expires_at": 'CREATE INDEX IF NOT EXISTS "ix_refresh_tokens_expires_at" ON "refresh_tokens"("expires_at")',
            "token_id": 'CREATE UNIQUE INDEX IF NOT EXISTS "ix_refresh_tokens_token_id" ON "refresh_tokens"("token_id")',
        },
        "index_names": {
            "user_id": "ix_refresh_tokens_user_id",
            "expires_at": "ix_refresh_tokens_expires_at",
            "token_id": "ix_refresh_tokens_token_id",
        },
        "create_table": (
            "CREATE TABLE IF NOT EXISTS \"refresh_tokens\"("
            '"id" SERIAL PRIMARY KEY,'
            '"token_id" VARCHAR(36) NOT NULL UNIQUE,'
            '"user_id" INTEGER NOT NULL REFERENCES "users"("id") ON DELETE CASCADE,'
            '"hashed_token" VARCHAR(255) NOT NULL,'
            '"expires_at" TIMESTAMPTZ NOT NULL,'
            '"revoked_at" TIMESTAMPTZ,'
            '"created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()'
            ")"
        ),
    },
    "audit_log": {
        "columns": [
            "id",
            "actor_user_id",
            "action",
            "target_type",
            "target_id",
            "metadata",
            "ip",
            "user_agent",
            "created_at",
        ],
        "auto_fix": {},
        "indexes": {
            "actor_user_id": 'CREATE INDEX IF NOT EXISTS "ix_audit_log_actor_user_id" ON "audit_log"("actor_user_id")',
            "created_at": 'CREATE INDEX IF NOT EXISTS "ix_audit_log_created_at" ON "audit_log"("created_at")',
        },
        "index_names": {
            "actor_user_id": "ix_audit_log_actor_user_id",
            "created_at": "ix_audit_log_created_at",
        },
        "create_table": (
            "CREATE TABLE IF NOT EXISTS \"audit_log\"("
            '"id" SERIAL PRIMARY KEY,'
            '"actor_user_id" INTEGER REFERENCES "users"("id") ON DELETE SET NULL,'
            '"action" VARCHAR(150) NOT NULL,'
            '"target_type" VARCHAR(100) NOT NULL,'
            '"target_id" VARCHAR(150),'
            "\"metadata\" JSON NOT NULL DEFAULT '{}',"
            '"ip" VARCHAR(64),'
            '"user_agent" VARCHAR(255),'
            '"created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()'
            ")"
        ),
    },
    # New tables added to schema
    "missions": {
        "columns": ["id", "objective", "status", "initiator_id", "active_plan_id", "created_at", "updated_at"],
        "auto_fix": {},
        "indexes": {
            "initiator_id": 'CREATE INDEX IF NOT EXISTS "ix_missions_initiator_id" ON "missions"("initiator_id")'
        },
        "index_names": {"initiator_id": "ix_missions_initiator_id"},
        "create_table": (
            "CREATE TABLE IF NOT EXISTS \"missions\"("
            '"id" SERIAL PRIMARY KEY,'
            '"objective" TEXT,'
            '"status" VARCHAR(50) DEFAULT \'pending\','
            '"initiator_id" INTEGER NOT NULL REFERENCES "users"("id"),'
            '"active_plan_id" INTEGER,'
            '"created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),'
            '"updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()'
            ")"
        )
    },
    "mission_plans": {
        "columns": ["id", "mission_id", "version", "planner_name", "status", "score", "rationale", "raw_json", "stats_json", "warnings_json", "content_hash", "created_at"],
        "auto_fix": {},
        "indexes": {
            "mission_id": 'CREATE INDEX IF NOT EXISTS "ix_mission_plans_mission_id" ON "mission_plans"("mission_id")'
        },
        "index_names": {"mission_id": "ix_mission_plans_mission_id"},
        "create_table": (
            "CREATE TABLE IF NOT EXISTS \"mission_plans\"("
            '"id" SERIAL PRIMARY KEY,'
            '"mission_id" INTEGER NOT NULL REFERENCES "missions"("id"),'
            '"version" INTEGER DEFAULT 1,'
            '"planner_name" VARCHAR(100) NOT NULL,'
            '"status" VARCHAR(50) DEFAULT \'draft\','
            '"score" FLOAT DEFAULT 0.0,'
            '"rationale" TEXT,'
            '"raw_json" TEXT,'
            '"stats_json" TEXT,'
            '"warnings_json" TEXT,'
            '"content_hash" VARCHAR(64),'
            '"created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()'
            ")"
        )
    },
    "tasks": {
        "columns": ["id", "mission_id", "plan_id", "task_key", "description", "tool_name", "tool_args_json", "status", "attempt_count", "max_attempts", "priority", "risk_level", "criticality", "depends_on_json", "result_text", "result_meta_json", "error_text", "started_at", "finished_at", "next_retry_at", "duration_ms", "created_at", "updated_at"],
        "auto_fix": {},
        "indexes": {
            "mission_id": 'CREATE INDEX IF NOT EXISTS "ix_tasks_mission_id" ON "tasks"("mission_id")',
            "plan_id": 'CREATE INDEX IF NOT EXISTS "ix_tasks_plan_id" ON "tasks"("plan_id")'
        },
        "index_names": {"mission_id": "ix_tasks_mission_id", "plan_id": "ix_tasks_plan_id"},
        "create_table": (
            "CREATE TABLE IF NOT EXISTS \"tasks\"("
            '"id" SERIAL PRIMARY KEY,'
            '"mission_id" INTEGER NOT NULL REFERENCES "missions"("id"),'
            '"plan_id" INTEGER REFERENCES "mission_plans"("id"),'
            '"task_key" VARCHAR(50) NOT NULL,'
            '"description" TEXT,'
            '"tool_name" VARCHAR(100),'
            '"tool_args_json" TEXT,'
            '"status" VARCHAR(50) DEFAULT \'pending\','
            '"attempt_count" INTEGER DEFAULT 0,'
            '"max_attempts" INTEGER DEFAULT 3,'
            '"priority" INTEGER DEFAULT 0,'
            '"risk_level" VARCHAR(50),'
            '"criticality" VARCHAR(50),'
            '"depends_on_json" TEXT,'
            '"result_text" TEXT,'
            '"result_meta_json" TEXT,'
            '"error_text" TEXT,'
            '"started_at" TIMESTAMPTZ,'
            '"finished_at" TIMESTAMPTZ,'
            '"next_retry_at" TIMESTAMPTZ,'
            '"duration_ms" INTEGER DEFAULT 0,'
            '"created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW(),'
            '"updated_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()'
            ")"
        )
    },
    "mission_events": {
        "columns": ["id", "mission_id", "event_type", "payload_json", "created_at"],
        "auto_fix": {},
        "indexes": {
             "mission_id": 'CREATE INDEX IF NOT EXISTS "ix_mission_events_mission_id" ON "mission_events"("mission_id")'
        },
        "index_names": {"mission_id": "ix_mission_events_mission_id"},
        "create_table": (
            "CREATE TABLE IF NOT EXISTS \"mission_events\"("
            '"id" SERIAL PRIMARY KEY,'
            '"mission_id" INTEGER NOT NULL REFERENCES "missions"("id"),'
            '"event_type" VARCHAR(50) NOT NULL,'
            '"payload_json" TEXT,'
            '"created_at" TIMESTAMPTZ NOT NULL DEFAULT NOW()'
            ")"
        )
    },
    "prompt_templates": {
        "columns": ["id", "name", "template"],
        "auto_fix": {},
        "indexes": {
            "name": 'CREATE UNIQUE INDEX IF NOT EXISTS "ix_prompt_templates_name" ON "prompt_templates"("name")'
        },
        "index_names": {"name": "ix_prompt_templates_name"},
        "create_table": (
            "CREATE TABLE IF NOT EXISTS \"prompt_templates\"("
            '"id" SERIAL PRIMARY KEY,'
            '"name" VARCHAR(255) NOT NULL UNIQUE,'
            '"template" TEXT NOT NULL'
            ")"
        )
    },
    "generated_prompts": {
        "columns": ["id", "prompt", "template_id"],
        "auto_fix": {},
        "indexes": {
            "template_id": 'CREATE INDEX IF NOT EXISTS "ix_generated_prompts_template_id" ON "generated_prompts"("template_id")'
        },
        "index_names": {"template_id": "ix_generated_prompts_template_id"},
        "create_table": (
            "CREATE TABLE IF NOT EXISTS \"generated_prompts\"("
            '"id" SERIAL PRIMARY KEY,'
            '"prompt" TEXT NOT NULL,'
            '"template_id" INTEGER NOT NULL REFERENCES "prompt_templates"("id")'
            ")"
        )
    }
}

def _to_sqlite_ddl(sql: str) -> str:
    """Converts PostgreSQL DDL to SQLite compatible DDL."""
    # Replace SERIAL with INTEGER PRIMARY KEY AUTOINCREMENT
    # Note: In CREATE TABLE, "id SERIAL PRIMARY KEY" becomes "id INTEGER PRIMARY KEY AUTOINCREMENT"
    sql = re.sub(r"SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT", sql, flags=re.IGNORECASE)

    # Replace TIMESTAMPTZ with TIMESTAMP or TEXT
    # SQLite has no TIMESTAMPTZ. TIMESTAMP is a safe generic type.
    sql = re.sub(r"TIMESTAMPTZ", "TIMESTAMP", sql, flags=re.IGNORECASE)

    # Replace JSON with TEXT
    sql = re.sub(r"JSON", "TEXT", sql, flags=re.IGNORECASE)

    # Replace BOOLEAN with INTEGER (or keep BOOLEAN as SQLite accepts it, but 0/1 is safer for defaults)
    # Handling Defaults: DEFAULT TRUE -> DEFAULT 1
    sql = re.sub(r"DEFAULT TRUE", "DEFAULT 1", sql, flags=re.IGNORECASE)
    sql = re.sub(r"DEFAULT FALSE", "DEFAULT 0", sql, flags=re.IGNORECASE)

    # Replace NOW() with CURRENT_TIMESTAMP
    sql = re.sub(r"NOW\(\)", "CURRENT_TIMESTAMP", sql, flags=re.IGNORECASE)

    # Replace IF NOT EXISTS in ADD COLUMN (SQLite doesn't support it in ALTER TABLE usually, removing it)
    # Postgres: ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...
    # SQLite: ALTER TABLE ... ADD COLUMN ... (fails if exists)
    sql = re.sub(r"ADD COLUMN IF NOT EXISTS", "ADD COLUMN", sql, flags=re.IGNORECASE)

    return sql

def _assert_schema_whitelist_alignment() -> None:
    """Ensures schema matches whitelist."""

    defined_tables = set(REQUIRED_SCHEMA.keys())
    undefined_tables = defined_tables - _ALLOWED_TABLES
    missing_definitions = _ALLOWED_TABLES - defined_tables

    if undefined_tables:
        raise ValueError(f"Unauthorized table in schema: {', '.join(sorted(undefined_tables))}")

    if missing_definitions:
        raise ValueError(f"Missing schema definition for allowed tables: {', '.join(sorted(missing_definitions))}")


_assert_schema_whitelist_alignment()

async def _get_existing_columns(conn: AsyncConnection, table_name: str) -> set[str]:
    """Extracts existing columns."""
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

async def _table_exists(conn: AsyncConnection, table_name: str) -> bool:
    """Checks if table exists."""

    dialect_name = conn.dialect.name

    if dialect_name == "sqlite":
        result = await conn.execute(
            text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"),
            {"table_name": table_name},
        )
        return result.fetchone() is not None

    result = await conn.execute(
        text(
            "SELECT EXISTS ("
            "SELECT FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = :table_name"
            ")"
        ),
        {"table_name": table_name},
    )
    return bool(result.scalar())

async def _fix_missing_column(
    conn: AsyncConnection,
    table_name: str,
    col: str,
    auto_fix_queries: dict[str, str],
    index_queries: dict[str, str],
) -> bool:
    """Fixes a missing column."""
    if col not in auto_fix_queries:
        return False

    query = auto_fix_queries[col]
    if conn.dialect.name == "sqlite":
        query = _to_sqlite_ddl(query)

    try:
        await conn.execute(text(query))
        logger.info(f"✅ Added missing column: {table_name}.{col}")

        if col in index_queries:
            idx_query = index_queries[col]
            # SQLite indexes are same syntax mostly, but ensure no Postgres specifics
            if conn.dialect.name == "sqlite":
                idx_query = _to_sqlite_ddl(idx_query)

            await conn.execute(text(idx_query))
            logger.info(f"✅ Created index for: {table_name}.{col}")

        return True
    except Exception as e:
        logger.error(f"❌ Failed to fix {table_name}.{col}: {e}")
        return False

def _infer_index_name(index_query: str) -> str | None:
    """Infers index name from SQL."""
    pattern = re.compile(r"INDEX(?: IF NOT EXISTS)?\s+\"([^\"]+)\"", flags=re.IGNORECASE)
    match = pattern.search(index_query)
    if match:
        return match.group(1)
    return None

async def _get_existing_indexes(conn: AsyncConnection, table_name: str) -> set[str]:
    """Gets existing index names."""
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
    """Ensures indexes exist."""
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
            if conn.dialect.name == "sqlite":
                index_query = _to_sqlite_ddl(index_query)

            await conn.execute(text(index_query))
            fixed_indexes.append(f"{table_name}.{index_name}")
            logger.info(f"✅ Created missing index: {table_name}.{index_name}")
        except Exception as exc:
            errors.append(f"Failed to create index {table_name}.{index_name}: {exc}")
            missing_indexes.append(f"{table_name}.{index_name}")

    return missing_indexes, fixed_indexes, errors

async def validate_and_fix_schema(auto_fix: bool = True) -> SchemaValidationResult:
    """
    Validates and fixes schema.
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

                table_exists = await _table_exists(conn, table_name)

                if not table_exists:
                    create_query = schema_info.get("create_table")

                    if create_query and auto_fix:
                        try:
                            if conn.dialect.name == "sqlite":
                                create_query = _to_sqlite_ddl(create_query)

                            await conn.execute(text(create_query))
                            logger.info(f"✅ Created missing table: {table_name}")
                            existing_columns = set(schema_info.get("columns", []))
                            results["fixed_columns"].extend(
                                [f"{table_name}.{col}" for col in existing_columns]
                            )
                            table_exists = True
                        except Exception as exc:
                            results["errors"].append(
                                f"Failed to create table {table_name}: {exc}"
                            )
                            continue
                    else:
                        results["errors"].append(
                            f"Table {table_name} is missing and cannot be auto-created"
                        )
                        continue

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
    Start-up Validation Hook.
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
