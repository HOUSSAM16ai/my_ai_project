# ======================================================================================
# ==                    API VALIDATION SCHEMAS (v1.0)                                ==
# ======================================================================================
# PRIME DIRECTIVE:
#   مخططات التحقق من صحة البيانات الخارقة - Enterprise validation schemas
#   ✨ المميزات:
#   - Schema definitions for all models
#   - Custom validators and field validation
#   - Automatic documentation support
#   - Type coercion and sanitization

from marshmallow import Schema, fields, validate, validates, ValidationError, post_load
from datetime import datetime
from typing import Any


# ======================================================================================
# PAGINATION & QUERY SCHEMAS
# ======================================================================================

class PaginationSchema(Schema):
    """Schema للترقيم - Pagination parameters"""
    page = fields.Integer(
        missing=1,
        validate=validate.Range(min=1),
        metadata={'description': 'Page number (starts from 1)'}
    )
    per_page = fields.Integer(
        missing=50,
        validate=validate.Range(min=1, max=100),
        metadata={'description': 'Items per page (max 100)'}
    )
    search = fields.String(
        required=False,
        allow_none=True,
        metadata={'description': 'Search query'}
    )
    order_by = fields.String(
        required=False,
        allow_none=True,
        metadata={'description': 'Field to order by'}
    )
    order_dir = fields.String(
        missing='asc',
        validate=validate.OneOf(['asc', 'desc']),
        metadata={'description': 'Order direction: asc or desc'}
    )


class QuerySchema(Schema):
    """Schema لاستعلامات SQL - SQL query validation"""
    sql = fields.String(
        required=True,
        validate=validate.Length(min=1, max=10000),
        metadata={'description': 'SQL query (SELECT only)'}
    )
    
    @validates('sql')
    def validate_sql(self, value):
        """التحقق من أن الاستعلام آمن - Validate SQL is safe"""
        sql_upper = value.strip().upper()
        if not sql_upper.startswith('SELECT'):
            raise ValidationError('Only SELECT queries are allowed')
        
        # Check for dangerous keywords
        dangerous_keywords = ['DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'TRUNCATE', 'EXEC']
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                raise ValidationError(f'Query contains forbidden keyword: {keyword}')


# ======================================================================================
# USER SCHEMA
# ======================================================================================

class UserSchema(Schema):
    """Schema للمستخدمين - User validation schema"""
    email = fields.Email(
        required=True,
        validate=validate.Length(max=120),
        metadata={'description': 'User email address'}
    )
    username = fields.String(
        required=True,
        validate=validate.Length(min=3, max=80),
        metadata={'description': 'Username (3-80 characters)'}
    )
    password = fields.String(
        load_only=True,
        required=True,
        validate=validate.Length(min=4),
        metadata={'description': 'Password (min 4 characters)'}
    )
    is_admin = fields.Boolean(
        missing=False,
        metadata={'description': 'Administrator flag'}
    )
    
    # Read-only fields
    id = fields.Integer(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    
    @validates('username')
    def validate_username(self, value):
        """التحقق من اسم المستخدم - Validate username"""
        if not value.replace('_', '').replace('-', '').isalnum():
            raise ValidationError('Username must contain only letters, numbers, hyphens and underscores')


# ======================================================================================
# MISSION SCHEMA
# ======================================================================================

class MissionSchema(Schema):
    """Schema للمهام - Mission validation schema"""
    objective = fields.String(
        required=True,
        validate=validate.Length(min=10, max=5000),
        metadata={'description': 'Mission objective (10-5000 characters)'}
    )
    status = fields.String(
        missing='PENDING',
        validate=validate.OneOf([
            'PENDING', 'PLANNED', 'IN_PROGRESS', 'BLOCKED', 
            'COMPLETED', 'FAILED', 'CANCELLED'
        ]),
        metadata={'description': 'Mission status'}
    )
    priority = fields.String(
        missing='MEDIUM',
        validate=validate.OneOf(['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']),
        metadata={'description': 'Mission priority'}
    )
    
    # Read-only fields
    id = fields.Integer(dump_only=True)
    initiator_id = fields.Integer(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    completed_at = fields.DateTime(dump_only=True)


# ======================================================================================
# TASK SCHEMA
# ======================================================================================

class TaskSchema(Schema):
    """Schema للمهام الفرعية - Task validation schema"""
    mission_id = fields.Integer(
        required=True,
        metadata={'description': 'Parent mission ID'}
    )
    task_key = fields.String(
        required=True,
        validate=validate.Length(min=1, max=128),
        metadata={'description': 'Unique task identifier'}
    )
    description = fields.String(
        required=True,
        validate=validate.Length(min=1, max=2000),
        metadata={'description': 'Task description'}
    )
    status = fields.String(
        missing='PENDING',
        validate=validate.OneOf([
            'PENDING', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'SKIPPED'
        ]),
        metadata={'description': 'Task status'}
    )
    depends_on_json = fields.List(
        fields.String(),
        missing=[],
        metadata={'description': 'List of task dependencies'}
    )
    
    # Read-only fields
    id = fields.Integer(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)
    completed_at = fields.DateTime(dump_only=True)


# ======================================================================================
# MISSION PLAN SCHEMA
# ======================================================================================

class MissionPlanSchema(Schema):
    """Schema لخطط المهام - Mission plan validation schema"""
    mission_id = fields.Integer(
        required=True,
        metadata={'description': 'Mission ID'}
    )
    plan_version = fields.Integer(
        missing=1,
        validate=validate.Range(min=1),
        metadata={'description': 'Plan version number'}
    )
    tasks_planned = fields.Integer(
        missing=0,
        validate=validate.Range(min=0),
        metadata={'description': 'Number of planned tasks'}
    )
    
    # Read-only fields
    id = fields.Integer(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


# ======================================================================================
# ADMIN CONVERSATION SCHEMA
# ======================================================================================

class AdminConversationSchema(Schema):
    """Schema لمحادثات الأدمن - Admin conversation validation schema"""
    title = fields.String(
        required=True,
        validate=validate.Length(min=1, max=500),
        metadata={'description': 'Conversation title'}
    )
    conversation_type = fields.String(
        missing='general',
        validate=validate.OneOf(['general', 'database', 'mission', 'support']),
        metadata={'description': 'Type of conversation'}
    )
    is_archived = fields.Boolean(
        missing=False,
        metadata={'description': 'Archive status'}
    )
    tags = fields.List(
        fields.String(),
        missing=[],
        metadata={'description': 'Conversation tags'}
    )
    
    # Read-only fields
    id = fields.Integer(dump_only=True)
    user_id = fields.Integer(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


# ======================================================================================
# ADMIN MESSAGE SCHEMA
# ======================================================================================

class AdminMessageSchema(Schema):
    """Schema لرسائل الأدمن - Admin message validation schema"""
    conversation_id = fields.Integer(
        required=True,
        metadata={'description': 'Conversation ID'}
    )
    role = fields.String(
        required=True,
        validate=validate.OneOf(['user', 'assistant', 'system']),
        metadata={'description': 'Message role'}
    )
    content = fields.String(
        required=True,
        validate=validate.Length(min=1, max=100000),
        metadata={'description': 'Message content'}
    )
    
    # Read-only fields
    id = fields.Integer(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    tokens_used = fields.Integer(dump_only=True)
    model_used = fields.String(dump_only=True)
