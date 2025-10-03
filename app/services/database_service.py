# app/services/database_service.py
# ======================================================================================
# ==                    DATABASE MANAGEMENT SERVICE (v1.0)                           ==
# ======================================================================================
# PRIME DIRECTIVE:
#   خدمة شاملة لإدارة قاعدة البيانات من صفحة الأدمن
#   - عرض جميع الجداول والبيانات
#   - CRUD operations على جميع الجداول
#   - استعلامات مخصصة
#   - تصدير واستيراد البيانات

from typing import List, Dict, Any, Optional
from sqlalchemy import inspect, text
from sqlalchemy.orm import class_mapper
from app import db
from app.models import (
    User, Subject, Lesson, Exercise, Submission,
    Mission, MissionPlan, Task, MissionEvent,
    AdminConversation, AdminMessage
)
import json
from datetime import datetime

# Map of all models
ALL_MODELS = {
    'users': User,
    'subjects': Subject,
    'lessons': Lesson,
    'exercises': Exercise,
    'submissions': Submission,
    'missions': Mission,
    'mission_plans': MissionPlan,
    'tasks': Task,
    'mission_events': MissionEvent,
    'admin_conversations': AdminConversation,
    'admin_messages': AdminMessage,
}

def get_all_tables() -> List[Dict[str, Any]]:
    """
    احصل على قائمة بجميع الجداول وإحصائياتها
    """
    tables = []
    
    for table_name, model in ALL_MODELS.items():
        try:
            count = db.session.query(model).count()
            mapper = class_mapper(model)
            columns = [col.key for col in mapper.columns]
            
            tables.append({
                'name': table_name,
                'model': model.__name__,
                'count': count,
                'columns': columns
            })
        except Exception as e:
            tables.append({
                'name': table_name,
                'model': model.__name__,
                'count': 0,
                'columns': [],
                'error': str(e)
            })
    
    return tables

def get_table_data(table_name: str, page: int = 1, per_page: int = 50, 
                   search: Optional[str] = None, order_by: Optional[str] = None,
                   order_dir: str = 'asc') -> Dict[str, Any]:
    """
    احصل على بيانات جدول معين مع الترقيم والبحث والترتيب
    """
    if table_name not in ALL_MODELS:
        return {'status': 'error', 'message': f'Table {table_name} not found'}
    
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
                if hasattr(col.type, 'python_type') and col.type.python_type == str:
                    search_filters.append(getattr(model, col.key).ilike(f'%{search}%'))
            if search_filters:
                from sqlalchemy import or_
                query = query.filter(or_(*search_filters))
        
        # Apply ordering
        if order_by and hasattr(model, order_by):
            order_col = getattr(model, order_by)
            if order_dir.lower() == 'desc':
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
                elif hasattr(value, 'value'):  # Enum
                    row[col] = value.value
                elif isinstance(value, (dict, list)):
                    row[col] = value
                else:
                    row[col] = str(value) if value is not None else None
            rows.append(row)
        
        return {
            'status': 'success',
            'table': table_name,
            'columns': columns,
            'rows': rows,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_record(table_name: str, record_id: int) -> Dict[str, Any]:
    """
    احصل على سجل واحد
    """
    if table_name not in ALL_MODELS:
        return {'status': 'error', 'message': f'Table {table_name} not found'}
    
    model = ALL_MODELS[table_name]
    
    try:
        record = db.session.get(model, record_id)
        if not record:
            return {'status': 'error', 'message': 'Record not found'}
        
        mapper = class_mapper(model)
        columns = [col.key for col in mapper.columns]
        
        data = {}
        for col in columns:
            value = getattr(record, col)
            if isinstance(value, datetime):
                data[col] = value.isoformat()
            elif hasattr(value, 'value'):
                data[col] = value.value
            elif isinstance(value, (dict, list)):
                data[col] = value
            else:
                data[col] = str(value) if value is not None else None
        
        return {'status': 'success', 'data': data}
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def create_record(table_name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    إنشاء سجل جديد
    """
    if table_name not in ALL_MODELS:
        return {'status': 'error', 'message': f'Table {table_name} not found'}
    
    model = ALL_MODELS[table_name]
    
    try:
        # Create new instance
        new_record = model(**data)
        db.session.add(new_record)
        db.session.commit()
        
        return {
            'status': 'success',
            'message': f'Record created in {table_name}',
            'id': new_record.id
        }
    except Exception as e:
        db.session.rollback()
        return {'status': 'error', 'message': str(e)}

def update_record(table_name: str, record_id: int, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    تحديث سجل موجود
    """
    if table_name not in ALL_MODELS:
        return {'status': 'error', 'message': f'Table {table_name} not found'}
    
    model = ALL_MODELS[table_name]
    
    try:
        record = db.session.get(model, record_id)
        if not record:
            return {'status': 'error', 'message': 'Record not found'}
        
        # Update fields
        for key, value in data.items():
            if hasattr(record, key):
                setattr(record, key, value)
        
        db.session.commit()
        
        return {
            'status': 'success',
            'message': f'Record {record_id} updated in {table_name}'
        }
    except Exception as e:
        db.session.rollback()
        return {'status': 'error', 'message': str(e)}

def delete_record(table_name: str, record_id: int) -> Dict[str, Any]:
    """
    حذف سجل
    """
    if table_name not in ALL_MODELS:
        return {'status': 'error', 'message': f'Table {table_name} not found'}
    
    model = ALL_MODELS[table_name]
    
    try:
        record = db.session.get(model, record_id)
        if not record:
            return {'status': 'error', 'message': 'Record not found'}
        
        db.session.delete(record)
        db.session.commit()
        
        return {
            'status': 'success',
            'message': f'Record {record_id} deleted from {table_name}'
        }
    except Exception as e:
        db.session.rollback()
        return {'status': 'error', 'message': str(e)}

def execute_query(sql: str) -> Dict[str, Any]:
    """
    تنفيذ استعلام SQL مخصص (للقراءة فقط)
    """
    # Security check - only allow SELECT queries
    sql_stripped = sql.strip().upper()
    if not sql_stripped.startswith('SELECT'):
        return {'status': 'error', 'message': 'Only SELECT queries are allowed'}
    
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
        
        return {
            'status': 'success',
            'columns': columns,
            'rows': rows,
            'count': len(rows)
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}

def get_database_stats() -> Dict[str, Any]:
    """
    احصل على إحصائيات شاملة لقاعدة البيانات
    """
    stats = {
        'tables': [],
        'total_records': 0
    }
    
    for table_name, model in ALL_MODELS.items():
        try:
            count = db.session.query(model).count()
            stats['tables'].append({
                'name': table_name,
                'count': count
            })
            stats['total_records'] += count
        except Exception as e:
            stats['tables'].append({
                'name': table_name,
                'count': 0,
                'error': str(e)
            })
    
    return stats

def export_table_data(table_name: str) -> Dict[str, Any]:
    """
    تصدير بيانات جدول بصيغة JSON
    """
    if table_name not in ALL_MODELS:
        return {'status': 'error', 'message': f'Table {table_name} not found'}
    
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
                elif hasattr(value, 'value'):
                    row[col] = value.value
                elif isinstance(value, (dict, list)):
                    row[col] = value
                else:
                    row[col] = str(value) if value is not None else None
            data.append(row)
        
        return {
            'status': 'success',
            'table': table_name,
            'count': len(data),
            'data': data
        }
    except Exception as e:
        return {'status': 'error', 'message': str(e)}
