# app/services/database_service.py
# ======================================================================================
# ==          DATABASE MANAGEMENT SERVICE (v3.0 - DI & Framework-Agnostic)          ==
# ======================================================================================
# PRIME DIRECTIVE:
#   A framework-agnostic, dependency-injected service for all database operations.
#   This service is designed for high performance, clarity, and zero coupling
#   to web frameworks like Flask or FastAPI.
#
# ✨ Key Features:
#   - Fully typed and documented methods.
#   - Accepts a SQLAlchemy Session via constructor for testability and flexibility.
#   - Handles CRUD, querying, schema inspection, and health checks.
#   - Replaces Flask-dependent globals with explicit dependencies.
#   - Includes backward-compatibility adapters to prevent breaking changes.

from __future__ import annotations

import enum
import math
from datetime import UTC, datetime, timedelta
from logging import Logger
from typing import Any

from sqlalchemy import func, inspect, select, text
from sqlalchemy.orm import Session, class_mapper

from app.config.settings import AppSettings as Settings
from app.core.di import get_logger, get_session, get_settings
from app.utils.model_registry import ModelRegistry


def _serialize_value(value: Any) -> Any:
    """Serializes values, correctly handling enums, datetimes, and other common types."""
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, enum.Enum):
        return value.value
    if isinstance(value, bool | int | str | float) or value is None:
        return value
    return str(value)


def _get_all_models():
    """Lazily load all models to reduce coupling."""
    return {
        "users": ModelRegistry.get_model("User"),
        "missions": ModelRegistry.get_model("Mission"),
        "mission_plans": ModelRegistry.get_model("MissionPlan"),
        "tasks": ModelRegistry.get_model("Task"),
        "mission_events": ModelRegistry.get_model("MissionEvent"),
        "admin_conversations": ModelRegistry.get_model("AdminConversation"),
        "admin_messages": ModelRegistry.get_model("AdminMessage"),
        "prompt_templates": ModelRegistry.get_model("PromptTemplate"),
        "generated_prompts": ModelRegistry.get_model("GeneratedPrompt"),
    }


_ALL_MODELS_CACHE = None


def get_all_models_registry():
    """Get all models, using cache if available."""
    global _ALL_MODELS_CACHE
    if _ALL_MODELS_CACHE is None:
        _ALL_MODELS_CACHE = _get_all_models()
    return _ALL_MODELS_CACHE


ALL_MODELS = get_all_models_registry()

MODEL_METADATA = {
    "users": {"icon": "👤", "category": "Core", "description": "User accounts and permissions"},
    "admin_conversations": {
        "icon": "💬",
        "category": "Admin",
        "description": "SUPERHUMAN admin conversations",
    },
    "admin_messages": {
        "icon": "✉️",
        "category": "Admin",
        "description": "Individual admin messages",
    },
    "prompt_templates": {
        "icon": "📜",
        "category": "Prompt Engineering",
        "description": "Reusable prompt templates",
    },
    "generated_prompts": {
        "icon": "✨",
        "category": "Prompt Engineering",
        "description": "History of generated prompts",
    },
    "missions": {"icon": "🎯", "category": "Overmind", "description": "AI missions"},
    "mission_plans": {
        "icon": "📋",
        "category": "Overmind",
        "description": "Mission execution plans",
    },
    "tasks": {"icon": "✅", "category": "Overmind", "description": "Mission tasks"},
    "mission_events": {"icon": "📊", "category": "Overmind", "description": "Mission event logs"},
}


class DatabaseService:
    """A framework-agnostic service for database operations."""

    def __init__(self, session: Session, logger: Logger, settings: Settings):
        self.session = session
        self.logger = logger
        self.settings = settings
        self._table_stats_cache = {}
        self._cache_timestamp = {}
        self.CACHE_TTL = 300  # 5 minutes

    def _validate_data(
        self, table_name: str, data: dict[str, Any], partial: bool = False
    ) -> tuple[bool, dict[str, Any] | list[str]]:
        """Helper function for data validation."""
        try:
            from app.validators import BaseValidator, schemas

            schema_map = {
                "users": "UserSchema",
                "missions": "MissionSchema",
                "tasks": "TaskSchema",
                "mission_plans": "MissionPlanSchema",
            }
            if table_name in schema_map:
                schema_class = getattr(schemas, schema_map[table_name], None)
                if schema_class:
                    success, validated_data, errors = BaseValidator.validate(
                        schema_class, data, partial=partial
                    )
                    if not success:
                        return False, errors
                    return True, validated_data
        except ImportError:
            self.logger.warning("Validators not available, skipping validation.")
        return True, data

    def get_database_health(self) -> dict[str, Any]:
        """Comprehensive database health check."""
        health = {
            "status": "healthy",
            "timestamp": datetime.now(UTC).isoformat(),
            "checks": {},
            "metrics": {},
            "warnings": [],
            "errors": [],
        }
        try:
            start = datetime.now(UTC)
            self.session.execute(text("SELECT 1"))
            connection_time = (datetime.now(UTC) - start).total_seconds() * 1000
            health["checks"]["connection"] = {
                "status": "ok",
                "latency_ms": round(connection_time, 2),
            }
            if connection_time > 100:
                health["warnings"].append(f"High connection latency: {connection_time:.2f}ms")

            engine = self.session.get_bind()
            inspector = inspect(engine)
            missing_tables = [name for name in ALL_MODELS if not inspector.has_table(name)]
            health["checks"]["tables"] = {
                "status": "ok" if not missing_tables else "error",
                "total": len(ALL_MODELS),
                "missing": missing_tables,
            }
            if missing_tables:
                health["status"] = "degraded"
                health["errors"].append(f"Missing tables: {', '.join(missing_tables)}")

            total_records, table_sizes = 0, {}
            for name, model in ALL_MODELS.items():
                try:
                    count = self.session.query(model).count()
                    total_records += count
                    table_sizes[name] = count
                except Exception as e:
                    health["warnings"].append(f"Could not count {name}: {str(e)}")
            health["metrics"].update({"total_records": total_records, "table_sizes": table_sizes})

        except Exception as e:
            self.logger.error(f"Database health check failed: {e}", exc_info=True)
            health["status"] = "error"
            health["errors"].append(f"Health check failed: {str(e)}")
        return health

    def get_table_schema(self, table_name: str) -> dict[str, Any]:
        """Get detailed table schema."""
        if table_name not in ALL_MODELS:
            return {"status": "error", "message": f"Table {table_name} not found"}
        model = ALL_MODELS[table_name]
        try:
            mapper = class_mapper(model)
            engine = self.session.get_bind()
            inspector = inspect(engine)
            columns = [
                {
                    "name": c.key,
                    "type": str(c.type),
                    "nullable": c.nullable,
                    "primary_key": c.primary_key,
                    "unique": c.unique,
                    "default": str(c.default) if c.default else None,
                }
                for c in mapper.columns
            ]
            indexes = [
                {"name": i["name"], "columns": i["column_names"], "unique": i.get("unique", False)}
                for i in inspector.get_indexes(table_name)
            ]
            foreign_keys = [
                {
                    "name": fk.get("name"),
                    "columns": fk["constrained_columns"],
                    "referred_table": fk["referred_table"],
                    "referred_columns": fk["referred_columns"],
                }
                for fk in inspector.get_foreign_keys(table_name)
            ]
            return {
                "status": "success",
                "table": table_name,
                "model": model.__name__,
                "columns": columns,
                "indexes": indexes,
                "foreign_keys": foreign_keys,
                "metadata": MODEL_METADATA.get(table_name, {}),
            }
        except Exception as e:
            self.logger.error(f"Error getting schema for table {table_name}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    def get_all_tables(self) -> list[dict[str, Any]]:
        """Get all tables with enhanced metadata."""
        cache_key = "all_tables"
        if (
            cache_key in self._table_stats_cache
            and (
                datetime.now(UTC) - self._cache_timestamp.get(cache_key, datetime.min)
            ).total_seconds()
            < self.CACHE_TTL
        ):
            return self._table_stats_cache[cache_key]

        tables = []
        for name, model in ALL_MODELS.items():
            try:
                count = self.session.query(model).count()
                columns = [c.key for c in class_mapper(model).columns]
                recent_count = (
                    self.session.query(model)
                    .filter(model.created_at >= datetime.now(UTC) - timedelta(days=1))
                    .count()
                    if hasattr(model, "created_at")
                    else 0
                )
                metadata = MODEL_METADATA.get(name, {})
                tables.append(
                    {
                        "name": name,
                        "model": model.__name__,
                        "count": count,
                        "recent_24h": recent_count,
                        "columns": columns,
                        "column_count": len(columns),
                        **metadata,
                    }
                )
            except Exception as e:
                self.logger.error(f"Error getting metadata for table {name}: {e}", exc_info=True)
                tables.append(
                    {
                        "name": name,
                        "model": model.__name__,
                        "error": str(e),
                        "icon": "⚠️",
                        "category": "Error",
                    }
                )

        tables.sort(key=lambda x: (x.get("category", "ZZZ"), x["name"]))
        self._table_stats_cache[cache_key] = tables
        self._cache_timestamp[cache_key] = datetime.now(UTC)
        return tables

    def _paginate(self, query, page, per_page):
        """Internal pagination helper."""
        total = self.session.execute(select(func.count()).select_from(query.subquery())).scalar()
        items = (
            self.session.execute(query.offset((page - 1) * per_page).limit(per_page))
            .scalars()
            .all()
        )
        return items, total, math.ceil(total / per_page) if total > 0 else 1

    def get_table_data(
        self,
        table_name: str,
        page: int = 1,
        per_page: int = 50,
        search: str | None = None,
        order_by: str | None = None,
        order_dir: str = "asc",
    ) -> dict[str, Any]:
        """Get paginated, searchable, and sortable data for a table."""
        if table_name not in ALL_MODELS:
            return {"status": "error", "message": f"Table {table_name} not found"}
        model = ALL_MODELS[table_name]
        try:
            query = select(model)
            if search:
                from sqlalchemy import or_

                search_filters = [
                    getattr(model, c.key).ilike(f"%{search}%")
                    for c in class_mapper(model).columns
                    if hasattr(c.type, "python_type") and c.type.python_type is str
                ]
                if search_filters:
                    query = query.where(or_(*search_filters))
            if order_by and hasattr(model, order_by):
                order_col = getattr(model, order_by)
                query = query.order_by(
                    order_col.desc() if order_dir.lower() == "desc" else order_col.asc()
                )

            total_items = self.session.execute(
                select(func.count()).select_from(query.alias())
            ).scalar()
            pages = math.ceil(total_items / per_page)

            paginated_query = query.limit(per_page).offset((page - 1) * per_page)

            items = self.session.execute(paginated_query).scalars().all()

            columns = [c.key for c in class_mapper(model).columns]

            rows = [{c: _serialize_value(getattr(item, c)) for c in columns} for item in items]
            return {
                "status": "success",
                "table": table_name,
                "columns": columns,
                "rows": rows,
                "total": total_items,
                "page": page,
                "per_page": per_page,
                "pages": pages,
            }
        except Exception as e:
            self.logger.error(f"Error getting data for table {table_name}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    def get_record(self, table_name: str, record_id: int) -> dict[str, Any]:
        """Get a single record."""
        if table_name not in ALL_MODELS:
            return {"status": "error", "message": f"Table {table_name} not found"}
        model = ALL_MODELS[table_name]
        try:
            record = self.session.get(model, record_id)
            if not record:
                return {"status": "error", "message": "Record not found"}
            columns = [c.key for c in class_mapper(model).columns]
            data = {c: _serialize_value(getattr(record, c)) for c in columns}
            return {"status": "success", "data": data}
        except Exception as e:
            self.logger.error(
                f"Error getting record {record_id} from {table_name}: {e}", exc_info=True
            )
            return {"status": "error", "message": str(e)}

    def create_record(self, table_name: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new record with validation."""
        if table_name not in ALL_MODELS:
            return {"status": "error", "message": f"Table {table_name} not found"}

        success, result = self._validate_data(table_name, data)
        if not success:
            return {"status": "error", "message": "Validation failed", "errors": result}

        model = ALL_MODELS[table_name]
        try:
            new_record = model(**result)
            self.session.add(new_record)
            self.session.commit()
            return {
                "status": "success",
                "message": f"Record created in {table_name}",
                "id": new_record.id,
            }
        except Exception as e:
            self.session.rollback()
            self.logger.error(f"Error creating record in {table_name}: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}

    def update_record(
        self, table_name: str, record_id: int, data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update an existing record with validation."""
        record = self.session.get(ALL_MODELS[table_name], record_id)
        if not record:
            return {"status": "error", "message": "Record not found"}

        success, result = self._validate_data(table_name, data, partial=True)
        if not success:
            return {"status": "error", "message": "Validation failed", "errors": result}

        try:
            for key, value in result.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            self.session.commit()
            return {"status": "success", "message": f"Record {record_id} updated in {table_name}"}
        except Exception as e:
            self.session.rollback()
            self.logger.error(
                f"Error updating record {record_id} in {table_name}: {e}", exc_info=True
            )
            return {"status": "error", "message": str(e)}

    def delete_record(self, table_name: str, record_id: int) -> dict[str, Any]:
        """Delete a record."""
        record = self.session.get(ALL_MODELS[table_name], record_id)
        if not record:
            return {"status": "error", "message": "Record not found"}

        try:
            self.session.delete(record)
            self.session.commit()
            return {"status": "success", "message": f"Record {record_id} deleted from {table_name}"}
        except Exception as e:
            self.session.rollback()
            self.logger.error(
                f"Error deleting record {record_id} from {table_name}: {e}", exc_info=True
            )
            return {"status": "error", "message": str(e)}

    def execute_query(self, sql: str) -> dict[str, Any]:
        """Execute a custom (read-only) SQL query."""
        if not sql.strip().upper().startswith("SELECT"):
            return {"status": "error", "message": "Only SELECT queries are allowed"}
        try:
            result = self.session.execute(text(sql))
            columns = list(result.keys())
            rows = [
                {columns[i]: _serialize_value(value) for i, value in enumerate(row)}
                for row in result.fetchall()
            ]
            return {"status": "success", "columns": columns, "rows": rows, "count": len(rows)}
        except Exception as e:
            self.logger.error(f"Error executing custom query: {e}", exc_info=True)
            return {"status": "error", "message": str(e)}


# ======================================================================================
# ==                            DEPENDENCY INJECTION FACTORY                          ==
# ======================================================================================

_database_service_singleton = None


def get_database_service() -> DatabaseService:
    """
    Factory function to get the singleton instance of the DatabaseService.
    """
    global _database_service_singleton
    if _database_service_singleton is None:
        _database_service_singleton = DatabaseService(
            session=get_session()(),  # get_session returns a factory
            logger=get_logger(),
            settings=get_settings(),
        )
    return _database_service_singleton


# ======================================================================================
# ==                         BACKWARD COMPATIBILITY ADAPTERS                          ==
# ======================================================================================
# These functions are deprecated and will be removed in a future version.
# They are provided for backward compatibility with existing code.


def get_database_health() -> dict[str, Any]:
    """Deprecated: replaced by DatabaseService.get_database_health."""
    return get_database_service().get_database_health()


def get_table_schema(table_name: str) -> dict[str, Any]:
    """Deprecated: replaced by DatabaseService.get_table_schema."""
    return get_database_service().get_table_schema(table_name)


def get_all_tables() -> list[dict[str, Any]]:
    """Deprecated: replaced by DatabaseService.get_all_tables."""
    return get_database_service().get_all_tables()


def get_table_data(
    table_name: str,
    page: int = 1,
    per_page: int = 50,
    search: str | None = None,
    order_by: str | None = None,
    order_dir: str = "asc",
) -> dict[str, Any]:
    """Deprecated: replaced by DatabaseService.get_table_data."""
    return get_database_service().get_table_data(
        table_name, page, per_page, search, order_by, order_dir
    )


def get_record(table_name: str, record_id: int) -> dict[str, Any]:
    """Deprecated: replaced by DatabaseService.get_record."""
    return get_database_service().get_record(table_name, record_id)


def create_record(table_name: str, data: dict[str, Any]) -> dict[str, Any]:
    """Deprecated: replaced by DatabaseService.create_record."""
    return get_database_service().create_record(table_name, data)


def update_record(table_name: str, record_id: int, data: dict[str, Any]) -> dict[str, Any]:
    """Deprecated: replaced by DatabaseService.update_record."""
    return get_database_service().update_record(table_name, record_id, data)


def delete_record(table_name: str, record_id: int) -> dict[str, Any]:
    """Deprecated: replaced by DatabaseService.delete_record."""
    return get_database_service().delete_record(table_name, record_id)


def execute_query(sql: str) -> dict[str, Any]:
    """Deprecated: replaced by DatabaseService.execute_query."""
    return get_database_service().execute_query(sql)
