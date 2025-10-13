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

import hashlib
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import func, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import class_mapper

from app import db
from app.models import Mission, MissionEvent, MissionPlan, Task, User

# ==================================================================================
# CONFIGURATION & MODEL REGISTRY 📋
# ==================================================================================

# Map of all models - النماذج المتاحة للإدارة
ALL_MODELS = {
    "users": User,
    "missions": Mission,
    "mission_plans": MissionPlan,
    "tasks": Task,
    "mission_events": MissionEvent,
}

# Model metadata - معلومات وصفية عن كل نموذج
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

# Query optimization cache - ذاكرة تخزين مؤقتة للأداء
_table_stats_cache = {}
_cache_timestamp = {}
CACHE_TTL = 300  # 5 minutes

# ==================================================================================
# ADVANCED DATABASE HEALTH & DIAGNOSTICS 🏥
# ==================================================================================


def get_database_health() -> Dict[str, Any]:
    """
    فحص صحة قاعدة البيانات الشامل - Comprehensive database health check
    Returns detailed health metrics and diagnostics
    """
    health = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "checks": {},
        "metrics": {},
        "warnings": [],
        "errors": [],
    }

    try:
        # 1. Connection test
        start = datetime.now(timezone.utc)
        db.session.execute(text("SELECT 1"))
        connection_time = (datetime.now(timezone.utc) - start).total_seconds() * 1000

        health["checks"]["connection"] = {"status": "ok", "latency_ms": round(connection_time, 2)}

        if connection_time > 100:
            health["warnings"].append(f"High connection latency: {connection_time:.2f}ms")

        # 2. Table integrity check
        missing_tables = []
        for table_name, model in ALL_MODELS.items():
            if not inspect(db.engine).has_table(table_name):
                missing_tables.append(table_name)

        health["checks"]["tables"] = {
            "status": "ok" if not missing_tables else "error",
            "total": len(ALL_MODELS),
            "missing": missing_tables,
        }

        if missing_tables:
            health["status"] = "degraded"
            health["errors"].append(f'Missing tables: {", ".join(missing_tables)}')

        # 3. Record counts and growth metrics
        total_records = 0
        table_sizes = {}
        for table_name, model in ALL_MODELS.items():
            try:
                count = db.session.query(model).count()
                total_records += count
                table_sizes[table_name] = count
            except Exception as e:
                health["warnings"].append(f"Could not count {table_name}: {str(e)}")

        health["metrics"]["total_records"] = total_records
        health["metrics"]["table_sizes"] = table_sizes

        # 4. Database size estimation (PostgreSQL specific)
        try:
            result = db.session.execute(
                text("SELECT pg_database_size(current_database())")
            ).scalar()
            health["metrics"]["database_size_bytes"] = result
            health["metrics"]["database_size_mb"] = round(result / 1024 / 1024, 2)
        except Exception:
            # Not PostgreSQL or permission issue
            pass

        # 5. Recent activity check (last 24 hours)
        try:
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            recent_missions = (
                db.session.query(Mission).filter(Mission.created_at >= yesterday).count()
            )
            recent_tasks = db.session.query(Task).filter(Task.created_at >= yesterday).count()

            health["metrics"]["recent_activity"] = {
                "missions_24h": recent_missions,
                "tasks_24h": recent_tasks,
            }
        except Exception as e:
            health["warnings"].append(f"Activity check failed: {str(e)}")

        # 6. Index health (if PostgreSQL)
        try:
            index_stats = db.session.execute(
                text(
                    """
                SELECT 
                    schemaname,
                    tablename,
                    COUNT(*) as index_count
                FROM pg_indexes 
                WHERE schemaname = 'public'
                GROUP BY schemaname, tablename
            """
                )
            ).fetchall()

            health["metrics"]["indexes"] = {row[1]: row[2] for row in index_stats}
        except Exception:
            # Not PostgreSQL or permission issue
            pass

    except Exception as e:
        health["status"] = "error"
        health["errors"].append(f"Health check failed: {str(e)}")

    return health


def optimize_database() -> Dict[str, Any]:
    """
    تحسين قاعدة البيانات - Database optimization
    Performs maintenance tasks like VACUUM, ANALYZE (PostgreSQL)
    """
    results = {"status": "success", "operations": [], "errors": []}

    try:
        # PostgreSQL optimization
        if db.engine.dialect.name == "postgresql":
            try:
                # ANALYZE to update statistics
                db.session.execute(text("ANALYZE"))
                results["operations"].append("ANALYZE completed")
            except Exception as e:
                results["errors"].append(f"ANALYZE failed: {str(e)}")

            # Clear query cache
            _table_stats_cache.clear()
            _cache_timestamp.clear()
            results["operations"].append("Cache cleared")

        # Commit session
        db.session.commit()

    except Exception as e:
        results["status"] = "error"
        results["errors"].append(f"Optimization failed: {str(e)}")

    return results


def get_table_schema(table_name: str) -> Dict[str, Any]:
    """
    الحصول على مخطط الجدول - Get detailed table schema
    Returns column information, constraints, indexes, etc.
    """
    if table_name not in ALL_MODELS:
        return {"status": "error", "message": f"Table {table_name} not found"}

    model = ALL_MODELS[table_name]

    try:
        mapper = class_mapper(model)
        inspector = inspect(db.engine)

        # Column information
        columns = []
        for col in mapper.columns:
            col_info = {
                "name": col.key,
                "type": str(col.type),
                "nullable": col.nullable,
                "primary_key": col.primary_key,
                "unique": col.unique,
                "default": str(col.default) if col.default else None,
            }
            columns.append(col_info)

        # Indexes
        indexes = []
        try:
            for idx in inspector.get_indexes(table_name):
                indexes.append(
                    {
                        "name": idx["name"],
                        "columns": idx["column_names"],
                        "unique": idx.get("unique", False),
                    }
                )
        except Exception:
            pass

        # Foreign keys
        foreign_keys = []
        try:
            for fk in inspector.get_foreign_keys(table_name):
                foreign_keys.append(
                    {
                        "name": fk.get("name"),
                        "columns": fk["constrained_columns"],
                        "referred_table": fk["referred_table"],
                        "referred_columns": fk["referred_columns"],
                    }
                )
        except Exception:
            pass

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


def get_all_tables() -> List[Dict[str, Any]]:
    """
    احصل على قائمة بجميع الجداول وإحصائياتها - Get all tables with enhanced metadata
    Includes caching, categorization, and rich metadata
    """
    tables = []

    # Check cache
    cache_key = "all_tables"
    if cache_key in _table_stats_cache:
        cache_time = _cache_timestamp.get(cache_key, datetime.min)
        if (datetime.now(timezone.utc) - cache_time).total_seconds() < CACHE_TTL:
            return _table_stats_cache[cache_key]

    for table_name, model in ALL_MODELS.items():
        try:
            count = db.session.query(model).count()
            mapper = class_mapper(model)
            columns = [col.key for col in mapper.columns]

            # Get recent activity
            recent_count = 0
            try:
                if hasattr(model, "created_at"):
                    yesterday = datetime.now(timezone.utc) - timedelta(days=1)
                    recent_count = (
                        db.session.query(model).filter(model.created_at >= yesterday).count()
                    )
            except Exception:
                pass

            metadata = MODEL_METADATA.get(table_name, {})

            tables.append(
                {
                    "name": table_name,
                    "model": model.__name__,
                    "count": count,
                    "recent_24h": recent_count,
                    "columns": columns,
                    "column_count": len(columns),
                    "icon": metadata.get("icon", "📁"),
                    "category": metadata.get("category", "Other"),
                    "description": metadata.get("description", "No description"),
                }
            )
        except Exception as e:
            tables.append(
                {
                    "name": table_name,
                    "model": model.__name__,
                    "count": 0,
                    "columns": [],
                    "column_count": 0,
                    "error": str(e),
                    "icon": "⚠️",
                    "category": "Error",
                }
            )

    # Sort by category and name
    tables.sort(key=lambda x: (x.get("category", "ZZZ"), x["name"]))

    # Update cache
    _table_stats_cache[cache_key] = tables
    _cache_timestamp[cache_key] = datetime.now(timezone.utc)

    return tables


def get_table_data(
    table_name: str,
    page: int = 1,
    per_page: int = 50,
    search: Optional[str] = None,
    order_by: Optional[str] = None,
    order_dir: str = "asc",
) -> Dict[str, Any]:
    """
    احصل على بيانات جدول معين مع الترقيم والبحث والترتيب
    """
    if table_name not in ALL_MODELS:
        return {"status": "error", "message": f"Table {table_name} not found"}

    model = ALL_MODELS[table_name]

    try:
        # Build query
        query = db.session.query(model)

        # Apply search if provided
        if search:
            mapper = class_mapper(model)
            search_filters = []
            for col in mapper.columns:
                # Search in string columns
                if hasattr(col.type, "python_type") and col.type.python_type == str:
                    search_filters.append(getattr(model, col.key).ilike(f"%{search}%"))
            if search_filters:
                from sqlalchemy import or_

                query = query.filter(or_(*search_filters))

        # Apply ordering
        if order_by and hasattr(model, order_by):
            order_col = getattr(model, order_by)
            if order_dir.lower() == "desc":
                query = query.order_by(order_col.desc())
            else:
                query = query.order_by(order_col.asc())

        # Get total count
        total = query.count()

        # Get paginated data
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        # Convert to dict
        mapper = class_mapper(model)
        columns = [col.key for col in mapper.columns]

        rows = []
        for item in pagination.items:
            row = {}
            for col in columns:
                value = getattr(item, col)
                # Handle special types
                if isinstance(value, datetime):
                    row[col] = value.isoformat()
                elif hasattr(value, "value"):  # Enum
                    row[col] = value.value
                elif isinstance(value, (dict, list)):
                    row[col] = value
                else:
                    row[col] = str(value) if value is not None else None
            rows.append(row)

        return {
            "status": "success",
            "table": table_name,
            "columns": columns,
            "rows": rows,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": pagination.pages,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_record(table_name: str, record_id: int) -> Dict[str, Any]:
    """
    احصل على سجل واحد
    """
    if table_name not in ALL_MODELS:
        return {"status": "error", "message": f"Table {table_name} not found"}

    model = ALL_MODELS[table_name]

    try:
        record = db.session.get(model, record_id)
        if not record:
            return {"status": "error", "message": "Record not found"}

        mapper = class_mapper(model)
        columns = [col.key for col in mapper.columns]

        data = {}
        for col in columns:
            value = getattr(record, col)
            if isinstance(value, datetime):
                data[col] = value.isoformat()
            elif hasattr(value, "value"):
                data[col] = value.value
            elif isinstance(value, (dict, list)):
                data[col] = value
            else:
                data[col] = str(value) if value is not None else None

        return {"status": "success", "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def create_record(table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    إنشاء سجل جديد - Create new record with validation
    """
    if table_name not in ALL_MODELS:
        return {"status": "error", "message": f"Table {table_name} not found"}

    model = ALL_MODELS[table_name]

    try:
        # Validate input data if schema exists
        try:
            from app.validators import BaseValidator

            schema_map = {
                "users": "UserSchema",
                "missions": "MissionSchema",
                "tasks": "TaskSchema",
                "mission_plans": "MissionPlanSchema",
            }

            if table_name in schema_map:
                schema_name = schema_map[table_name]
                from app.validators import schemas

                schema_class = getattr(schemas, schema_name, None)

                if schema_class:
                    success, validated_data, errors = BaseValidator.validate(schema_class, data)
                    if not success:
                        return {"status": "error", "message": "Validation failed", "errors": errors}
                    # Use validated data
                    data = validated_data
        except ImportError:
            # Validators not available, proceed without validation
            pass

        # Create new instance
        new_record = model(**data)
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


def update_record(table_name: str, record_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    تحديث سجل موجود - Update existing record with validation
    """
    if table_name not in ALL_MODELS:
        return {"status": "error", "message": f"Table {table_name} not found"}

    model = ALL_MODELS[table_name]

    try:
        # Validate input data if schema exists (partial update)
        try:
            from app.validators import BaseValidator

            schema_map = {
                "users": "UserSchema",
                "missions": "MissionSchema",
                "tasks": "TaskSchema",
                "mission_plans": "MissionPlanSchema",
            }

            if table_name in schema_map:
                schema_name = schema_map[table_name]
                from app.validators import schemas

                schema_class = getattr(schemas, schema_name, None)

                if schema_class:
                    success, validated_data, errors = BaseValidator.validate(
                        schema_class, data, partial=True
                    )
                    if not success:
                        return {"status": "error", "message": "Validation failed", "errors": errors}
                    # Use validated data
                    data = validated_data
        except ImportError:
            # Validators not available, proceed without validation
            pass

        record = db.session.get(model, record_id)
        if not record:
            return {"status": "error", "message": "Record not found"}

        # Update fields
        for key, value in data.items():
            if hasattr(record, key):
                setattr(record, key, value)

        db.session.commit()

        return {"status": "success", "message": f"Record {record_id} updated in {table_name}"}
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}


def delete_record(table_name: str, record_id: int) -> Dict[str, Any]:
    """
    حذف سجل
    """
    if table_name not in ALL_MODELS:
        return {"status": "error", "message": f"Table {table_name} not found"}

    model = ALL_MODELS[table_name]

    try:
        record = db.session.get(model, record_id)
        if not record:
            return {"status": "error", "message": "Record not found"}

        db.session.delete(record)
        db.session.commit()

        return {"status": "success", "message": f"Record {record_id} deleted from {table_name}"}
    except Exception as e:
        db.session.rollback()
        return {"status": "error", "message": str(e)}


def execute_query(sql: str) -> Dict[str, Any]:
    """
    تنفيذ استعلام SQL مخصص (للقراءة فقط)
    """
    # Security check - only allow SELECT queries
    sql_stripped = sql.strip().upper()
    if not sql_stripped.startswith("SELECT"):
        return {"status": "error", "message": "Only SELECT queries are allowed"}

    try:
        result = db.session.execute(text(sql))
        rows = []
        columns = list(result.keys()) if result.returns_rows else []

        if result.returns_rows:
            for row in result:
                row_dict = {}
                for i, col in enumerate(columns):
                    value = row[i]
                    if isinstance(value, datetime):
                        row_dict[col] = value.isoformat()
                    else:
                        row_dict[col] = str(value) if value is not None else None
                rows.append(row_dict)

        return {"status": "success", "columns": columns, "rows": rows, "count": len(rows)}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_database_stats() -> Dict[str, Any]:
    """
    احصل على إحصائيات شاملة لقاعدة البيانات
    """
    stats = {"tables": [], "total_records": 0}

    for table_name, model in ALL_MODELS.items():
        try:
            count = db.session.query(model).count()
            stats["tables"].append({"name": table_name, "count": count})
            stats["total_records"] += count
        except Exception as e:
            stats["tables"].append({"name": table_name, "count": 0, "error": str(e)})

    return stats


def export_table_data(table_name: str) -> Dict[str, Any]:
    """
    تصدير بيانات جدول بصيغة JSON
    """
    if table_name not in ALL_MODELS:
        return {"status": "error", "message": f"Table {table_name} not found"}

    model = ALL_MODELS[table_name]

    try:
        records = db.session.query(model).all()
        mapper = class_mapper(model)
        columns = [col.key for col in mapper.columns]

        data = []
        for record in records:
            row = {}
            for col in columns:
                value = getattr(record, col)
                if isinstance(value, datetime):
                    row[col] = value.isoformat()
                elif hasattr(value, "value"):
                    row[col] = value.value
                elif isinstance(value, (dict, list)):
                    row[col] = value
                else:
                    row[col] = str(value) if value is not None else None
            data.append(row)

        return {"status": "success", "table": table_name, "count": len(data), "data": data}
    except Exception as e:
        return {"status": "error", "message": str(e)}
