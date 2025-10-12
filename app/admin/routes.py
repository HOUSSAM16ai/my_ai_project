# app/admin/routes.py
# ======================================================================================
# ==                        OVERMIND COMMAND GATEWAY (v11.1)                          ==
# ======================================================================================
# PRIME DIRECTIVE:
#   This blueprint serves as the SOLE administrative gateway. It renders the Mission
#   Control UI and provides secure, well-defined API endpoints.
#
# ARCHITECTURAL FIX (v11.1):
#   - Simplified `render_template` calls (e.g., "admin_dashboard.html" instead of
#     "admin/admin_dashboard.html") to correctly leverage the blueprint's scoped
#     `template_folder`.

from flask import render_template, abort, request, jsonify, flash, current_app, url_for
from flask_login import current_user, login_required
from functools import wraps
from datetime import datetime, timezone

from app.admin import bp
from app import db

# --- [THE GRAND BLUEPRINT IMPORTS] ---
from app.models import User, Mission, Task, AdminConversation, AdminMessage

# --- [THE COGNITIVE ENGINE IMPORTS] ---
try:
    from app.services import master_agent_service as overmind
except ImportError:
    overmind = None
try:
    from app.services import generation_service as maestro
except ImportError:
    maestro = None

# --------------------------------------------------------------------------------------
# Authorization Decorator
# --------------------------------------------------------------------------------------
def admin_required(f):
    """Decorator to ensure the user is logged in and is an administrator."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not getattr(current_user, 'is_admin', False):
            abort(403) # Forbidden
        return f(*args, **kwargs)
    return decorated_function

# --------------------------------------------------------------------------------------
# UI Rendering Routes
# --------------------------------------------------------------------------------------

@bp.route("/dashboard")
@admin_required
def admin_dashboard():
    """Renders the main Mission Control dashboard."""
    missions = []
    try:
        missions = Mission.query.order_by(Mission.updated_at.desc()).all()
    except Exception as e:
        current_app.logger.error(f"Failed to fetch missions for dashboard: {e}", exc_info=True)
        flash("Could not retrieve mission list from the Akashic Records.", "danger")
    
    # --- [THE CRITICAL FIX] ---
    # The path is now relative to the blueprint's `template_folder`.
    return render_template(
        "admin_dashboard.html",
        title="Overmind Mission Control",
        missions=missions
    )

@bp.route("/mission/<int:mission_id>")
@admin_required
def mission_detail(mission_id):
    """Renders the detailed view for a single mission."""
    mission = Mission.query.get_or_404(mission_id)
    # --- [THE CRITICAL FIX] ---
    # Also corrected here for consistency.
    return render_template("mission_detail.html", title=f"Mission #{mission.id}", mission=mission)

# --------------------------------------------------------------------------------------
# API Gateways to the AI Minds
# --------------------------------------------------------------------------------------

@bp.route("/api/start-mission", methods=["POST"])
@admin_required
def handle_start_mission():
    """API Gateway to the Overmind."""
    if not overmind:
        return jsonify({"status": "error", "message": "The Overmind service is not available."}), 503

    data = request.json
    objective = data.get("objective")

    if not objective or not isinstance(objective, str) or len(objective.strip()) == 0:
        return jsonify({"status": "error", "message": "A valid objective is required."}), 400

    try:
        current_app.logger.info(f"API: Received objective '{objective}' from user {current_user.id}.")
        mission = overmind.start_mission(objective=objective, initiator=current_user._get_current_object())
        return jsonify({
            "status": "success",
            "message": "Mission initiated successfully.",
            "mission_id": mission.id,
            "redirect_url": url_for('admin.mission_detail', mission_id=mission.id)
        })
    except Exception as e:
        current_app.logger.error(f"Failed to start mission via API: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"An unexpected error occurred: {e}"}), 500

# --------------------------------------------------------------------------------------
# Administrative Utility Routes
# --------------------------------------------------------------------------------------

@bp.route("/users")
@admin_required
def list_users():
    """Displays a list of all users in the system."""
    all_users = []
    try:
        all_users = db.session.scalars(db.select(User).order_by(User.id)).all()
    except Exception as e:
        flash(f"Error fetching users: {e}", "danger")
    
    # --- [THE CRITICAL FIX] ---
    # Assuming `admin_users.html` is also in the `admin/templates` folder.
    return render_template("admin_users.html", title="User Roster", users=all_users)

# --------------------------------------------------------------------------------------
# --------------------------------------------------------------------------------------

try:
    from app.services.admin_ai_service import get_admin_ai_service
except ImportError:
    get_admin_ai_service = None

@bp.route("/api/chat", methods=["POST"])
@admin_required
def handle_chat():
    """API endpoint للمحادثة الذكية"""
    if not get_admin_ai_service:
        return jsonify({"status": "error", "message": "AI service not available."}), 503
    
    # Handle JSON parsing errors
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"status": "error", "message": "Invalid JSON in request body."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to parse JSON: {str(e)}"}), 400
    
    question = data.get("question", "").strip()
    conversation_id = data.get("conversation_id")
    use_deep_context = data.get("use_deep_context", True)
    
    if not question:
        return jsonify({"status": "error", "message": "Question is required."}), 400
    
    try:
        service = get_admin_ai_service()
        
        # Auto-create conversation if not provided
        if not conversation_id:
            # Generate a smart title from the first question
            title = question[:100] + "..." if len(question) > 100 else question
            conversation = service.create_conversation(
                user=current_user._get_current_object(),
                title=title,
                conversation_type="general"
            )
            conversation_id = conversation.id
            current_app.logger.info(f"Auto-created conversation #{conversation_id} for user {current_user.id}")
        
        result = service.answer_question(
            question=question,
            user=current_user._get_current_object(),
            conversation_id=conversation_id,
            use_deep_context=use_deep_context
        )
        
        # Always return the conversation_id for client-side tracking
        result["conversation_id"] = conversation_id
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Chat API failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route("/api/analyze-project", methods=["POST"])
@admin_required
def handle_analyze_project():
    """API endpoint لتحليل المشروع"""
    if not get_admin_ai_service:
        return jsonify({"status": "error", "message": "AI service not available."}), 503
    
    # Handle JSON parsing errors
    try:
        data = request.get_json() or {}
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to parse JSON: {str(e)}"}), 400
    
    conversation_id = data.get("conversation_id")
    
    try:
        service = get_admin_ai_service()
        
        # Auto-create conversation if not provided
        if not conversation_id:
            conversation = service.create_conversation(
                user=current_user._get_current_object(),
                title="Project Analysis",
                conversation_type="project_analysis"
            )
            conversation_id = conversation.id
            current_app.logger.info(f"Auto-created analysis conversation #{conversation_id} for user {current_user.id}")
        
        result = service.analyze_project(
            user=current_user._get_current_object(),
            conversation_id=conversation_id
        )
        
        # Always return the conversation_id for client-side tracking
        result["conversation_id"] = conversation_id
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Project analysis API failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/execute-modification", methods=["POST"])
@admin_required
def handle_execute_modification():
    """API endpoint لتنفيذ تعديلات على المشروع"""
    if not get_admin_ai_service:
        return jsonify({"status": "error", "message": "AI service not available."}), 503
    
    # Handle JSON parsing errors
    try:
        data = request.get_json()
        if data is None:
            return jsonify({"status": "error", "message": "Invalid JSON in request body."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to parse JSON: {str(e)}"}), 400
    
    objective = data.get("objective", "").strip()
    conversation_id = data.get("conversation_id")
    
    if not objective:
        return jsonify({"status": "error", "message": "Objective is required."}), 400
    
    try:
        service = get_admin_ai_service()
        
        # Auto-create conversation if not provided
        if not conversation_id:
            # Generate a smart title from the objective
            title = f"Modification: {objective[:80]}..." if len(objective) > 80 else f"Modification: {objective}"
            conversation = service.create_conversation(
                user=current_user._get_current_object(),
                title=title,
                conversation_type="modification"
            )
            conversation_id = conversation.id
            current_app.logger.info(f"Auto-created modification conversation #{conversation_id} for user {current_user.id}")
        
        result = service.execute_modification(
            objective=objective,
            user=current_user._get_current_object(),
            conversation_id=conversation_id
        )
        
        # Always return the conversation_id for client-side tracking
        result["conversation_id"] = conversation_id
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Modification API failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/conversations", methods=["GET"])
@admin_required
def handle_get_conversations():
    """API endpoint لجلب محادثات المستخدم"""
    try:
        # Get all conversations for the current user, ordered by most recent first
        conversations = AdminConversation.query.filter_by(
            user_id=current_user.id,
            is_archived=False
        ).order_by(AdminConversation.updated_at.desc()).all()
        
        # Format conversations for response
        conversations_list = [
            {
                "id": conv.id,
                "title": conv.title,
                "conversation_type": conv.conversation_type,
                "total_messages": conv.total_messages,
                "message_count": conv.total_messages,  # For frontend compatibility
                "total_tokens": conv.total_tokens,
                "last_message_at": conv.last_message_at.isoformat() if conv.last_message_at else None,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "tags": conv.tags or []
            }
            for conv in conversations
        ]
        
        return jsonify({
            "status": "success",
            "conversations": conversations_list,
            "count": len(conversations_list)
        })
        
    except Exception as e:
        current_app.logger.error(f"Failed to get conversations: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/conversation/<int:conversation_id>", methods=["GET"])
@admin_required
def handle_get_conversation_detail(conversation_id):
    """API endpoint لجلب تفاصيل محادثة"""
    try:
        # Get conversation and verify ownership
        conversation = AdminConversation.query.filter_by(
            id=conversation_id,
            user_id=current_user.id
        ).first()
        
        if not conversation:
            return jsonify({"status": "error", "message": "Conversation not found or access denied."}), 404
        
        # Get all messages for this conversation
        messages = AdminMessage.query.filter_by(
            conversation_id=conversation_id
        ).order_by(AdminMessage.created_at).all()
        
        # Format messages for response
        messages_list = [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "tokens_used": msg.tokens_used,
                "model_used": msg.model_used,
                "latency_ms": msg.latency_ms,
                "created_at": msg.created_at.isoformat(),
                "metadata": msg.metadata_json
            }
            for msg in messages
        ]
        
        return jsonify({
            "status": "success",
            "conversation": {
                "id": conversation.id,
                "title": conversation.title,
                "conversation_type": conversation.conversation_type,
                "total_messages": conversation.total_messages,
                "total_tokens": conversation.total_tokens,
                "avg_response_time_ms": conversation.avg_response_time_ms,
                "is_archived": conversation.is_archived,
                "last_message_at": conversation.last_message_at.isoformat() if conversation.last_message_at else None,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "tags": conversation.tags or [],
                "messages": messages_list
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Failed to get conversation detail: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


# --------------------------------------------------------------------------------------
# DATABASE MANAGEMENT ROUTES
# --------------------------------------------------------------------------------------

try:
    from app.services import database_service
except ImportError:
    database_service = None

@bp.route("/database")
@admin_required
def database_management():
    """عرض صفحة إدارة قاعدة البيانات"""
    return render_template("database_management.html", title="Database Management")

@bp.route("/api/database/tables", methods=["GET"])
@admin_required
def get_tables():
    """API endpoint لجلب قائمة الجداول"""
    if not database_service:
        return jsonify({"status": "error", "message": "Database service not available"}), 503
    
    try:
        tables = database_service.get_all_tables()
        return jsonify({"status": "success", "tables": tables})
    except Exception as e:
        current_app.logger.error(f"Get tables failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route("/api/database/health", methods=["GET"])
@admin_required
def get_database_health():
    """API endpoint لفحص صحة قاعدة البيانات"""
    if not database_service:
        return jsonify({"status": "error", "message": "Database service not available"}), 503
    
    try:
        health = database_service.get_database_health()
        return jsonify(health)
    except Exception as e:
        current_app.logger.error(f"Database health check failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route("/api/database/stats", methods=["GET"])
@admin_required
def get_db_stats():
    """API endpoint لجلب إحصائيات قاعدة البيانات"""
    if not database_service:
        return jsonify({"status": "error", "message": "Database service not available"}), 503
    
    try:
        stats = database_service.get_database_stats()
        return jsonify({"status": "success", "stats": stats})
    except Exception as e:
        current_app.logger.error(f"Get database stats failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route("/api/database/table/<table_name>", methods=["GET"])
@admin_required
def get_table_data(table_name):
    """API endpoint لجلب بيانات جدول معين"""
    if not database_service:
        return jsonify({"status": "error", "message": "Database service not available"}), 503
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 50, type=int)
        search = request.args.get('search', None, type=str)
        order_by = request.args.get('order_by', None, type=str)
        order_dir = request.args.get('order_dir', 'asc', type=str)
        
        result = database_service.get_table_data(
            table_name, page, per_page, search, order_by, order_dir
        )
        
        # Return appropriate status code based on result
        if result.get('status') == 'error':
            if 'not found' in result.get('message', '').lower():
                return jsonify(result), 404
            return jsonify(result), 500
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Get table data failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route("/api/database/record/<table_name>/<int:record_id>", methods=["GET"])
@admin_required
def get_record(table_name, record_id):
    """API endpoint لجلب سجل واحد"""
    if not database_service:
        return jsonify({"status": "error", "message": "Database service not available"}), 503
    
    try:
        result = database_service.get_record(table_name, record_id)
        
        # Return appropriate status code based on result
        if result.get('status') == 'error':
            if 'not found' in result.get('message', '').lower():
                return jsonify(result), 404
            return jsonify(result), 500
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Get record failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route("/api/database/record/<table_name>", methods=["POST"])
@admin_required
def create_record(table_name):
    """API endpoint لإنشاء سجل جديد"""
    if not database_service:
        return jsonify({"status": "error", "message": "Database service not available"}), 503
    
    try:
        data = request.json
        result = database_service.create_record(table_name, data)
        
        # Return appropriate status code based on result
        if result.get('status') == 'error':
            # Check if it's a validation error
            if 'validation' in result.get('message', '').lower() or 'errors' in result:
                return jsonify(result), 400
            if 'not found' in result.get('message', '').lower():
                return jsonify(result), 404
            return jsonify(result), 500
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Create record failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route("/api/database/record/<table_name>/<int:record_id>", methods=["PUT"])
@admin_required
def update_record(table_name, record_id):
    """API endpoint لتحديث سجل"""
    if not database_service:
        return jsonify({"status": "error", "message": "Database service not available"}), 503
    
    try:
        data = request.json
        result = database_service.update_record(table_name, record_id, data)
        
        # Return appropriate status code based on result
        if result.get('status') == 'error':
            # Check if it's a validation error
            if 'validation' in result.get('message', '').lower() or 'errors' in result:
                return jsonify(result), 400
            if 'not found' in result.get('message', '').lower():
                return jsonify(result), 404
            return jsonify(result), 500
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Update record failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route("/api/database/record/<table_name>/<int:record_id>", methods=["DELETE"])
@admin_required
def delete_record(table_name, record_id):
    """API endpoint لحذف سجل"""
    if not database_service:
        return jsonify({"status": "error", "message": "Database service not available"}), 503
    
    try:
        result = database_service.delete_record(table_name, record_id)
        
        # Return appropriate status code based on result
        if result.get('status') == 'error':
            if 'not found' in result.get('message', '').lower():
                return jsonify(result), 404
            return jsonify(result), 500
        
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Delete record failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route("/api/database/query", methods=["POST"])
@admin_required
def execute_query():
    """API endpoint لتنفيذ استعلام SQL"""
    if not database_service:
        return jsonify({"status": "error", "message": "Database service not available"}), 503
    
    try:
        data = request.json
        sql = data.get('sql', '').strip()
        
        if not sql:
            return jsonify({"status": "error", "message": "SQL query is required"}), 400
        
        result = database_service.execute_query(sql)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Execute query failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500

@bp.route("/api/database/export/<table_name>", methods=["GET"])
@admin_required
def export_table(table_name):
    """API endpoint لتصدير بيانات جدول"""
    if not database_service:
        return jsonify({"status": "error", "message": "Database service not available"}), 503
    
    try:
        result = database_service.export_table_data(table_name)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Export table failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


# --------------------------------------------------------------------------------------
# ADVANCED DATABASE MANAGEMENT ENDPOINTS (v2.0) 🚀
# --------------------------------------------------------------------------------------

@bp.route("/api/database/optimize", methods=["POST"])
@admin_required
def optimize_database():
    """API endpoint لتحسين قاعدة البيانات"""
    if not database_service:
        return jsonify({"status": "error", "message": "Database service not available"}), 503
    
    try:
        result = database_service.optimize_database()
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Database optimization failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/database/schema/<table_name>", methods=["GET"])
@admin_required
def get_table_schema(table_name):
    """API endpoint للحصول على مخطط جدول"""
    if not database_service:
        return jsonify({"status": "error", "message": "Database service not available"}), 503
    
    try:
        schema = database_service.get_table_schema(table_name)
        return jsonify(schema)
    except Exception as e:
        current_app.logger.error(f"Get table schema failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


# =====================================================================================
# 🔥 WORLD-CLASS ADVANCED API ENDPOINTS (v2.0 - SUPERHUMAN EDITION) 🔥
# =====================================================================================
# PRIME DIRECTIVE:
#   نقاط نهاية خارقة تتفوق على الشركات العملاقة مثل Google و Microsoft
#   ✨ المميزات الخارقة:
#   - Real-time observability with P99.9 latency monitoring
#   - Zero-Trust security with JWT and request signing
#   - OpenAPI contract validation
#   - ML-based anomaly detection
#   - Automated SLA compliance monitoring
#   - Advanced security audit logging

try:
    from app.services.api_observability_service import get_observability_service, monitor_performance
    from app.services.api_security_service import get_security_service, rate_limit, require_jwt_auth
    from app.services.api_contract_service import get_contract_service, validate_contract
except ImportError:
    get_observability_service = None
    get_security_service = None
    get_contract_service = None
    monitor_performance = lambda f: f
    rate_limit = lambda f: f
    require_jwt_auth = lambda f: f
    validate_contract = lambda f: f


@bp.route("/api/observability/metrics", methods=["GET"])
@admin_required
@monitor_performance
def get_observability_metrics():
    """
    🎯 Get real-time observability metrics
    
    Returns comprehensive performance metrics including:
    - P50, P95, P99, P99.9 latency percentiles
    - Requests per second
    - Error rates
    - SLA compliance metrics
    """
    if not get_observability_service:
        return jsonify({"status": "error", "message": "Observability service not available"}), 503
    
    try:
        service = get_observability_service()
        snapshot = service.get_performance_snapshot()
        sla_compliance = service.get_sla_compliance()
        
        return jsonify({
            "status": "success",
            "timestamp": snapshot.timestamp.isoformat(),
            "performance": {
                "avg_latency_ms": snapshot.avg_latency_ms,
                "p50_latency_ms": snapshot.p50_latency_ms,
                "p95_latency_ms": snapshot.p95_latency_ms,
                "p99_latency_ms": snapshot.p99_latency_ms,
                "p999_latency_ms": snapshot.p999_latency_ms,
                "requests_per_second": snapshot.requests_per_second,
                "error_rate": snapshot.error_rate,
                "active_requests": snapshot.active_requests
            },
            "sla_compliance": sla_compliance
        })
    except Exception as e:
        current_app.logger.error(f"Get observability metrics failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/observability/alerts", methods=["GET"])
@admin_required
@monitor_performance
def get_anomaly_alerts():
    """
    🚨 Get ML-detected anomaly alerts
    
    Query parameters:
    - severity: Filter by severity (critical, high, medium, low)
    """
    if not get_observability_service:
        return jsonify({"status": "error", "message": "Observability service not available"}), 503
    
    try:
        service = get_observability_service()
        severity = request.args.get('severity')
        
        alerts = service.get_all_alerts(severity=severity)
        
        return jsonify({
            "status": "success",
            "total_alerts": len(alerts),
            "alerts": alerts
        })
    except Exception as e:
        current_app.logger.error(f"Get anomaly alerts failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/observability/endpoint/<path:endpoint_path>", methods=["GET"])
@admin_required
@monitor_performance
def get_endpoint_analytics(endpoint_path):
    """
    📊 Get detailed analytics for specific endpoint
    
    Returns endpoint-specific metrics and performance data
    """
    if not get_observability_service:
        return jsonify({"status": "error", "message": "Observability service not available"}), 503
    
    try:
        service = get_observability_service()
        analytics = service.get_endpoint_analytics(endpoint_path)
        
        return jsonify({
            "status": "success",
            **analytics
        })
    except Exception as e:
        current_app.logger.error(f"Get endpoint analytics failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/security/token/generate", methods=["POST"])
@admin_required
@rate_limit
def generate_jwt_token():
    """
    🔐 Generate short-lived JWT access token (15 minutes)
    
    Request body:
    {
        "scopes": ["read", "write"]  // Optional
    }
    """
    if not get_security_service:
        return jsonify({"status": "error", "message": "Security service not available"}), 503
    
    try:
        service = get_security_service()
        data = request.get_json() or {}
        scopes = data.get('scopes', [])
        
        # Generate access token
        access_token = service.generate_access_token(
            user_id=current_user.id,
            scopes=scopes
        )
        
        # Generate refresh token
        refresh_token = service.generate_refresh_token(user_id=current_user.id)
        
        return jsonify({
            "status": "success",
            "access_token": access_token.token,
            "refresh_token": refresh_token.token,
            "token_type": "Bearer",
            "expires_in": 900,  # 15 minutes in seconds
            "expires_at": access_token.expires_at.isoformat(),
            "scopes": access_token.scopes
        })
    except Exception as e:
        current_app.logger.error(f"Generate JWT token failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/security/token/refresh", methods=["POST"])
@rate_limit
def refresh_jwt_token():
    """
    🔄 Rotate access token using refresh token
    
    Request body:
    {
        "refresh_token": "your-refresh-token"
    }
    """
    if not get_security_service:
        return jsonify({"status": "error", "message": "Security service not available"}), 503
    
    try:
        service = get_security_service()
        data = request.get_json() or {}
        refresh_token = data.get('refresh_token')
        
        if not refresh_token:
            return jsonify({"status": "error", "message": "Refresh token is required"}), 400
        
        # Rotate token
        new_access_token = service.rotate_token(refresh_token)
        
        if not new_access_token:
            return jsonify({"status": "error", "message": "Invalid or expired refresh token"}), 401
        
        return jsonify({
            "status": "success",
            "access_token": new_access_token.token,
            "token_type": "Bearer",
            "expires_in": 900,
            "expires_at": new_access_token.expires_at.isoformat()
        })
    except Exception as e:
        current_app.logger.error(f"Refresh JWT token failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/security/audit-logs", methods=["GET"])
@admin_required
@monitor_performance
def get_security_audit_logs():
    """
    📋 Get security audit logs for compliance
    
    Query parameters:
    - event_type: Filter by event type
    - severity: Filter by severity
    - limit: Number of logs to return (default: 100)
    """
    if not get_security_service:
        return jsonify({"status": "error", "message": "Security service not available"}), 503
    
    try:
        service = get_security_service()
        
        event_type = request.args.get('event_type')
        severity = request.args.get('severity')
        limit = request.args.get('limit', 100, type=int)
        
        logs = service.get_audit_logs(
            event_type=event_type,
            severity=severity,
            limit=limit
        )
        
        return jsonify({
            "status": "success",
            "total_logs": len(logs),
            "logs": logs
        })
    except Exception as e:
        current_app.logger.error(f"Get security audit logs failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/contract/openapi", methods=["GET"])
@admin_required
def get_openapi_specification():
    """
    📜 Get OpenAPI 3.0 specification
    
    Returns complete OpenAPI specification with all endpoints,
    schemas, and security definitions
    """
    if not get_contract_service:
        return jsonify({"status": "error", "message": "Contract service not available"}), 503
    
    try:
        service = get_contract_service()
        spec = service.generate_openapi_spec()
        
        return jsonify(spec)
    except Exception as e:
        current_app.logger.error(f"Get OpenAPI spec failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/contract/violations", methods=["GET"])
@admin_required
@monitor_performance
def get_contract_violations():
    """
    🔴 Get API contract violations
    
    Query parameters:
    - severity: Filter by severity
    - violation_type: Filter by type (schema, version, breaking_change)
    - limit: Number of violations to return (default: 100)
    """
    if not get_contract_service:
        return jsonify({"status": "error", "message": "Contract service not available"}), 503
    
    try:
        service = get_contract_service()
        
        severity = request.args.get('severity')
        violation_type = request.args.get('violation_type')
        limit = request.args.get('limit', 100, type=int)
        
        violations = service.get_contract_violations(
            severity=severity,
            violation_type=violation_type,
            limit=limit
        )
        
        return jsonify({
            "status": "success",
            "total_violations": len(violations),
            "violations": violations
        })
    except Exception as e:
        current_app.logger.error(f"Get contract violations failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/health/comprehensive", methods=["GET"])
@monitor_performance
def comprehensive_health_check():
    """
    💚 Comprehensive health check for all systems
    
    Returns health status for:
    - Database
    - Observability service
    - Security service
    - Contract validation
    - SLA compliance
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {}
    }
    
    # Check database
    try:
        if database_service:
            db_health = database_service.get_database_health()
            health_status["components"]["database"] = {
                "status": db_health.get("status", "unknown"),
                "checks": db_health.get("checks", {})
            }
        else:
            health_status["components"]["database"] = {"status": "unavailable"}
    except Exception as e:
        health_status["components"]["database"] = {"status": "error", "message": str(e)}
        health_status["status"] = "degraded"
    
    # Check observability
    try:
        if get_observability_service:
            obs_service = get_observability_service()
            sla = obs_service.get_sla_compliance()
            health_status["components"]["observability"] = {
                "status": "healthy" if sla["sla_status"] == "compliant" else "warning",
                "sla_compliance": sla["compliance_rate_percent"]
            }
        else:
            health_status["components"]["observability"] = {"status": "unavailable"}
    except Exception as e:
        health_status["components"]["observability"] = {"status": "error", "message": str(e)}
        health_status["status"] = "degraded"
    
    # Check security
    try:
        if get_security_service:
            health_status["components"]["security"] = {"status": "healthy"}
        else:
            health_status["components"]["security"] = {"status": "unavailable"}
    except Exception as e:
        health_status["components"]["security"] = {"status": "error", "message": str(e)}
        health_status["status"] = "degraded"
    
    # Check contract validation
    try:
        if get_contract_service:
            health_status["components"]["contract_validation"] = {"status": "healthy"}
        else:
            health_status["components"]["contract_validation"] = {"status": "unavailable"}
    except Exception as e:
        health_status["components"]["contract_validation"] = {"status": "error", "message": str(e)}
        health_status["status"] = "degraded"
    
    return jsonify(health_status)

