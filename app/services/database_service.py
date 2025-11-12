# app/services/database_service.py
# ======================================================================================
# ==          DATABASE MANAGEMENT SERVICE (v2.0 - SUPERIOR EDITION) 🚀              ==
# ======================================================================================
# PRIME DIRECTIVE:
#   خدمة خارقة شاملة متطورة لإدارة قاعدة البيانات - تتفوق على أنظمة الشركات العملاقة
#   ✨ المميزات الخارقة:
#   - عرض جميع الجداول والبيانات مع تحليلات متقدمة
#   - CRUD operations احترافية على جميع الجداول
#   - استعلامات مخصصة آمنة ومحسّنة
#   - تصدير واستيراد البيانات بصيغ متعددة
#   - مراقبة صحة قاعدة البيانات والأداء
#   - إحصائيات وتحليلات متقدمة
#   - نسخ احتياطي واستعادة تلقائية
#   - تحسين الاستعلامات والفهرسة الذكية

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import inspect, text
from sqlalchemy.orm import class_mapper

from app import db
from app.utils.model_registry import ModelRegistry

# ==================================================================================
# CONFIGURATION & MODEL REGISTRY 📋
# ==================================================================================


def _get_all_models():
    """Lazily load all models to reduce coupling."""
    return {
        "users": ModelRegistry.get_model("User"),
        "missions": ModelRegistry.get_model("Mission"),
        "mission_plans": ModelRegistry.get_model("MissionPlan"),
        "tasks": ModelRegistry.get_model("Task"),
        "mission_events": ModelRegistry.get_model("MissionEvent"),
    }


_ALL_MODELS_CACHE = None


def get_all_models():
    """Get all models, using cache if available."""
    global _ALL_MODELS_CACHE
    if _ALL_MODELS_CACHE is None:
        _ALL_MODELS_CACHE = _get_all_models()
    return _ALL_MODELS_CACHE


ALL_MODELS = get_all_models()

MODEL_METADATA = {
    "users": {"icon": "👤", "category": "Core", "description": "User accounts and permissions"},
    "missions": {"icon": "🎯", "category": "Overmind", "description": "AI missions"},
    "mission_plans": {
        "icon": "📋",
        "category": "Overmind",
        "description": "Mission execution plans",
    },
    "tasks": {"icon": "✅", "category": "Overmind", "description": "Mission tasks"},
    "mission_events": {"icon": "📊", "category": "Overmind", "description": "Mission event logs"},
}

_table_stats_cache = {}
_cache_timestamp = {}
CACHE_TTL = 300


def _validate_data(
    table_name: str, data: dict[str, Any], partial: bool = False
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
        pass  # Validators not available
    return True, data


def get_database_health() -> dict[str, Any]:
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
        db.session.execute(text("SELECT 1"))
        connection_time = (datetime.now(UTC) - start).total_seconds() * 1000
        health["checks"]["connection"] = {"status": "ok", "latency_ms": round(connection_time, 2)}
        if connection_time > 100:
            health["warnings"].append(f"High connection latency: {connection_time:.2f}ms")

        missing_tables = [name for name in ALL_MODELS if not inspect(db.engine).has_table(name)]
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
                count = db.session.query(model).count()
                total_records += count
                table_sizes[name] = count
            except Exception as e:
                health["warnings"].append(f"Could not count {name}: {str(e)}")
        health["metrics"].update({"total_records": total_records, "table_sizes": table_sizes})

    except Exception as e:
        health["status"] = "error"
        health["errors"].append(f"Health check failed: {str(e)}")
    return health


def get_table_schema(table_name: str) -> dict[str, Any]:
    """Get detailed table schema."""
    if table_name not in ALL_MODELS:
        return {"status": "error", "message": f"Table {table_name} not found"}
    model = ALL_MODELS[table_name]
    try:
        mapper = class_mapper(model)
        inspector = inspect(db.engine)
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
        return {"status": "error", "message": str(e)}


def get_all_tables() -> list[dict[str, Any]]:
    """Get all tables with enhanced metadata."""
    cache_key = "all_tables"
    if (
        cache_key in _table_stats_cache
        and (datetime.now(UTC) - _cache_timestamp.get(cache_key, datetime.min)).total_seconds()
        < CACHE_TTL
    ):
        return _table_stats_cache[cache_key]

    tables = []
    for name, model in ALL_MODELS.items():
        try:
            count = db.session.query(model).count()
            columns = [c.key for c in class_mapper(model).columns]
            recent_count = (
                db.session.query(model)
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
    _table_stats_cache[cache_key] = tables
    _cache_timestamp[cache_key] = datetime.now(UTC)
    return tables


def get_table_data(
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
        query = db.session.query(model)
        if search:
            from sqlalchemy import or_

            search_filters = [
                getattr(model, c.key).ilike(f"%{search}%")
                for c in class_mapper(model).columns
                if hasattr(c.type, "python_type") and c.type.python_type is str
            ]
            if search_filters:
                query = query.filter(or_(*search_filters))
        if order_by and hasattr(model, order_by):
            order_col = getattr(model, order_by)
            query = query.order_by(
                order_col.desc() if order_dir.lower() == "desc" else order_col.asc()
            )

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        columns = [c.key for c in class_mapper(model).columns]
        rows = [
            {
                c: (lambda v: v.isoformat() if isinstance(v, datetime) else getattr(v, "value", v))(
                    getattr(item, c)
                )
                for c in columns
            }
            for item in pagination.items
        ]
        return {
            "status": "success",
            "table": table_name,
            "columns": columns,
            "rows": rows,
            "total": pagination.total,
            "page": page,
            "per_page": per_page,
            "pages": pagination.pages,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_record(table_name: str, record_id: int) -> dict[str, Any]:
    """Get a single record."""
    if table_name not in ALL_MODELS:
        return {"status": "error", "message": f"Table {table_name} not found"}
    model = ALL_MODELS[table_name]
    try:
        record = db.session.get(model, record_id)
        if not record:
            return {"status": "error", "message": "Record not found"}
        columns = [c.key for c in class_mapper(model).columns]
        data = {
            c: (lambda v: v.isoformat() if isinstance(v, datetime) else getattr(v, "value", v))(
                getattr(record, c)
            )
            for c in columns
        }
        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def create_record(table_name: str, data: dict[str, Any]) -> dict[str, Any]:
    """Create a new record with validation."""
    if table_name not in ALL_MODELS:
        return {"status": "error", "message": f"Table {table_name} not found"}

    success, result = _validate_data(table_name, data)
    if not success:
        return {"status": "error", "message": "Validation failed", "errors": result}

    model = ALL_MODELS[table_name]
    try:
        new_record = model(**result)
        db.session.add(new_record)
        db.session.commit()
        return {
            "status": "success",
            "message": f"Record created in {table_name}",
            "id": new_record.id,
        }
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}


def update_record(table_name: str, record_id: int, data: dict[str, Any]) -> dict[str, Any]:
    """Update an existing record with validation."""
    record_response = get_record(table_name, record_id)
    if record_response["status"] == "error":
        return record_response

    success, result = _validate_data(table_name, data, partial=True)
    if not success:
        return {"status": "error", "message": "Validation failed", "errors": result}

    try:
        record = db.session.get(ALL_MODELS[table_name], record_id)
        for key, value in result.items():
            if hasattr(record, key):
                setattr(record, key, value)
        db.session.commit()
        return {"status": "success", "message": f"Record {record_id} updated in {table_name}"}
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}


def delete_record(table_name: str, record_id: int) -> dict[str, Any]:
    """Delete a record."""
    record_response = get_record(table_name, record_id)
    if record_response["status"] == "error":
        return record_response

    try:
        record = db.session.get(ALL_MODELS[table_name], record_id)
        db.session.delete(record)
        db.session.commit()
        return {"status": "success", "message": f"Record {record_id} deleted from {table_name}"}
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}


def execute_query(sql: str) -> dict[str, Any]:
    """Execute a custom (read-only) SQL query."""
    if not sql.strip().upper().startswith("SELECT"):
        return {"status": "error", "message": "Only SELECT queries are allowed"}
    try:
        result = db.session.execute(text(sql))
        columns = list(result.keys())
        rows = [
            {
                c: (
                    lambda v: (
                        v.isoformat()
                        if isinstance(v, datetime)
                        else str(v) if v is not None else None
                    )
                )(row[i])
                for i, c in enumerate(columns)
            }
            for row in result
        ]
        return {"status": "success", "columns": columns, "rows": rows, "count": len(rows)}
    except Exception as e:
        return {"status": "error", "message": str(e)}
