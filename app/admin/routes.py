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

from app.admin import bp
from app import db

# --- [THE GRAND BLUEPRINT IMPORTS] ---
from app.models import User, Mission, Task

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
    from app.models import AdminConversation, AdminMessage
except ImportError:
    get_admin_ai_service = None
    AdminConversation = None
    AdminMessage = None

@bp.route("/api/chat", methods=["POST"])
@admin_required
def handle_chat():
    """API endpoint للمحادثة الذكية"""
    if not get_admin_ai_service:
        return jsonify({"status": "error", "message": "AI service not available."}), 503
    
    data = request.json
    question = data.get("question", "").strip()
    conversation_id = data.get("conversation_id")
    use_deep_context = data.get("use_deep_context", True)
    
    if not question:
        return jsonify({"status": "error", "message": "Question is required."}), 400
    
    try:
        service = get_admin_ai_service()
        
        if not conversation_id:
            conv = service.create_conversation(
                user=current_user._get_current_object(),
                title=question[:100],
                conversation_type="general"
            )
            conversation_id = conv.id
        
        result = service.answer_question(
            question=question,
            user=current_user._get_current_object(),
            conversation_id=conversation_id,
            use_deep_context=use_deep_context
        )
        
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
    
    data = request.json or {}
    conversation_id = data.get("conversation_id")
    
    try:
        service = get_admin_ai_service()
        result = service.analyze_project(
            user=current_user._get_current_object(),
            conversation_id=conversation_id
        )
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
    
    data = request.json
    objective = data.get("objective", "").strip()
    conversation_id = data.get("conversation_id")
    
    if not objective:
        return jsonify({"status": "error", "message": "Objective is required."}), 400
    
    try:
        service = get_admin_ai_service()
        result = service.execute_modification(
            objective=objective,
            user=current_user._get_current_object(),
            conversation_id=conversation_id
        )
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Modification API failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/conversations", methods=["GET"])
@admin_required
def handle_get_conversations():
    """API endpoint لجلب محادثات المستخدم"""
    if not get_admin_ai_service:
        return jsonify({"status": "error", "message": "AI service not available."}), 503
    
    try:
        service = get_admin_ai_service()
        conversations = service.get_user_conversations(
            user=current_user._get_current_object()
        )
        
        return jsonify({
            "status": "success",
            "conversations": [
                {
                    "id": conv.id,
                    "title": conv.title,
                    "type": conv.conversation_type,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                    "message_count": len(conv.messages)
                }
                for conv in conversations
            ]
        })
        
    except Exception as e:
        current_app.logger.error(f"Get conversations API failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/conversation/<int:conversation_id>", methods=["GET"])
@admin_required
def handle_get_conversation_detail(conversation_id):
    """API endpoint لجلب تفاصيل محادثة"""
    try:
        if not AdminConversation:
            return jsonify({"status": "error", "message": "Admin conversations not available."}), 503
            
        conv = db.session.get(AdminConversation, conversation_id)
        
        if not conv or conv.user_id != current_user.id:
            return jsonify({"status": "error", "message": "Conversation not found."}), 404
        
        return jsonify({
            "status": "success",
            "conversation": {
                "id": conv.id,
                "title": conv.title,
                "type": conv.conversation_type,
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "created_at": msg.created_at.isoformat(),
                        "tokens_used": msg.tokens_used,
                        "model_used": msg.model_used
                    }
                    for msg in conv.messages
                ]
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"Get conversation detail failed: {e}", exc_info=True)
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
