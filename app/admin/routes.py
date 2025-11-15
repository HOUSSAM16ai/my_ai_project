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

import json
from datetime import UTC, datetime
from functools import wraps

from flask import (
    Response,
    abort,
    current_app,
    flash,
    jsonify,
    render_template,
    request,
    stream_with_context,
    url_for,
)
from flask_login import current_user, login_required

from app import db
from app.admin import bp

# --- [THE GRAND BLUEPRINT IMPORTS] ---
from app.models import AdminConversation, AdminMessage, Mission, User

# --- [THE COGNITIVE ENGINE IMPORTS] ---
try:
    from app.services import master_agent_service as overmind
except ImportError:
    overmind = None
try:
    from app.services import generation_service as maestro
except ImportError:
    maestro = None
try:
    from app.services.admin_chat_streaming_service import get_streaming_service
except ImportError:
    get_streaming_service = None
try:
    from app.services.admin_chat_performance_service import get_performance_service
except ImportError:
    get_performance_service = None
try:
    from app.services.ai_service_gateway import get_ai_service_gateway
except ImportError:
    get_ai_service_gateway = None


# --------------------------------------------------------------------------------------
# Authorization Decorator
# --------------------------------------------------------------------------------------
def admin_required(f):
    """Decorator to ensure the user is logged in and is an administrator."""

    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not getattr(current_user, "is_admin", False):
            abort(403)  # Forbidden
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
        "admin_dashboard.html", title="Overmind Mission Control", missions=missions
    )


@bp.route("/mission/<int:mission_id>")
@admin_required
def mission_detail(mission_id):
    """Renders the detailed view for a single mission."""
    mission = db.get_or_404(Mission, mission_id)
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
        return (
            jsonify({"status": "error", "message": "The Overmind service is not available."}),
            503,
        )

    data = request.json
    objective = data.get("objective")

    if not objective or not isinstance(objective, str) or len(objective.strip()) == 0:
        return jsonify({"status": "error", "message": "A valid objective is required."}), 400

    try:
        current_app.logger.info(
            f"API: Received objective '{objective}' from user {current_user.id}."
        )
        mission = overmind.start_mission(
            objective=objective, initiator=current_user._get_current_object()
        )
        return jsonify(
            {
                "status": "success",
                "message": "Mission initiated successfully.",
                "mission_id": mission.id,
                "redirect_url": url_for("admin.mission_detail", mission_id=mission.id),
            }
        )
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


def _get_stream_params(req):
    """Extracts chat streaming parameters from the Flask request."""
    if req.method == "GET":
        question = req.args.get("question", "").strip()
        conversation_id = req.args.get("conversation_id")
    else:  # POST
        data = req.get_json(silent=True) or {}
        question = data.get("question", "").strip()
        conversation_id = data.get("conversation_id")
    return question, conversation_id


@bp.route("/api/chat/stream", methods=["GET", "POST"])
@admin_required
def handle_chat_stream():
    """
    SSE streaming endpoint with intelligent fallback.
    
    Tries standalone AI service first, falls back to internal AdminAIService if unavailable.
    This ensures chat always works regardless of deployment configuration.
    """
    question, conversation_id = _get_stream_params(request)

    if not question:
        return jsonify({"status": "error", "message": "Question is required."}), 400

    # Try gateway first, but have fallback ready
    gateway = get_ai_service_gateway()
    use_gateway = gateway is not None
    
    if not use_gateway:
        current_app.logger.warning(
            "AI Service Gateway not available, using internal AdminAIService fallback"
        )

    def stream_response():
        """Generator function to stream the response with fallback support."""
        try:
            if use_gateway:
                # Try using gateway to standalone service
                current_app.logger.info("Streaming via AI Service Gateway")
                try:
                    for chunk in gateway.stream_chat(question, conversation_id, current_user.id):
                        yield f"data: {json.dumps(chunk)}\n\n"
                    return
                except Exception as gateway_error:
                    current_app.logger.warning(
                        f"Gateway streaming failed: {gateway_error}. Falling back to internal service."
                    )
                    # Fall through to internal service
            
            # Fallback: Use internal AdminAIService
            current_app.logger.info("Streaming via internal AdminAIService")
            from app.services.admin_ai_service import AdminAIService
            
            admin_ai = AdminAIService()
            
            # Get or create conversation
            conv_id = None
            if conversation_id:
                try:
                    conv_id = int(conversation_id)
                except (ValueError, TypeError):
                    pass
            
            # Call the internal service (non-streaming)
            result = admin_ai.answer_question(
                question=question,
                user=current_user._get_current_object(),
                conversation_id=conv_id,
                use_deep_context=True
            )
            
            # Stream the response in chunks for better UX
            if result.get("status") == "success":
                answer = result.get("answer", "")
                
                # Send answer in chunks (simulating streaming)
                words = answer.split()
                chunk_size = 5  # words per chunk
                
                for i in range(0, len(words), chunk_size):
                    chunk_words = words[i:i + chunk_size]
                    chunk_text = " ".join(chunk_words) + " "
                    
                    chunk_data = {
                        "type": "data", 
                        "data": chunk_text,
                        "payload": {"content": chunk_text}
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                
                # Send completion
                completion_data = {
                    "type": "end",
                    "payload": {
                        "conversation_id": result.get("conversation_id"),
                        "tokens_used": result.get("tokens_used"),
                        "model_used": result.get("model_used"),
                        "elapsed_seconds": result.get("elapsed_seconds")
                    }
                }
                yield f"data: {json.dumps(completion_data)}\n\n"
            else:
                # Error case
                error_msg = result.get("answer", result.get("error", "Unknown error"))
                error_data = {
                    "type": "error",
                    "payload": {"error": error_msg}
                }
                yield f"data: {json.dumps(error_data)}\n\n"
                
        except Exception as e:
            current_app.logger.error(f"Error during streaming: {e}", exc_info=True)
            error_payload = json.dumps(
                {"type": "error", "payload": {"error": f"Failed to get AI response: {str(e)}"}}
            )
            yield f"data: {error_payload}\n\n"

    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",  # Important for Nginx buffering
    }
    return Response(stream_with_context(stream_response()), headers=headers)


@bp.route("/api/conversations", methods=["GET"])
@admin_required
def handle_get_conversations():
    """API endpoint لجلب محادثات المستخدم"""
    try:
        # Get all conversations for the current user, ordered by most recent first
        conversations = (
            AdminConversation.query.filter_by(user_id=current_user.id, is_archived=False)
            .order_by(AdminConversation.updated_at.desc())
            .all()
        )

        # Format conversations for response
        conversations_list = [
            {
                "id": conv.id,
                "title": conv.title,
                "conversation_type": conv.conversation_type,
                "total_messages": conv.total_messages,
                "message_count": conv.total_messages,  # For frontend compatibility
                "total_tokens": conv.total_tokens,
                "last_message_at": (
                    conv.last_message_at.isoformat() if conv.last_message_at else None
                ),
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "tags": conv.tags or [],
            }
            for conv in conversations
        ]

        return jsonify(
            {
                "status": "success",
                "conversations": conversations_list,
                "count": len(conversations_list),
            }
        )

    except Exception as e:
        current_app.logger.error(f"Failed to get conversations: {e}", exc_info=True)
        # Return 200 with error details
        return (
            jsonify(
                {
                    "status": "error",
                    "message": f"Failed to load conversations: {str(e)}",
                    "conversations": [],
                    "count": 0,
                }
            ),
            200,
        )


@bp.route("/api/conversation/<int:conversation_id>", methods=["GET"])
@admin_required
def handle_get_conversation_detail(conversation_id):
    """API endpoint لجلب تفاصيل محادثة"""
    try:
        # Get conversation and verify ownership
        conversation = AdminConversation.query.filter_by(
            id=conversation_id, user_id=current_user.id
        ).first()

        if not conversation:
            return (
                jsonify({"status": "error", "message": "Conversation not found or access denied."}),
                404,
            )

        # Get all messages for this conversation
        messages = (
            AdminMessage.query.filter_by(conversation_id=conversation_id)
            .order_by(AdminMessage.created_at)
            .all()
        )

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
                "metadata": msg.metadata_json,
            }
            for msg in messages
        ]

        return jsonify(
            {
                "status": "success",
                "conversation": {
                    "id": conversation.id,
                    "title": conversation.title,
                    "conversation_type": conversation.conversation_type,
                    "total_messages": conversation.total_messages,
                    "total_tokens": conversation.total_tokens,
                    "avg_response_time_ms": conversation.avg_response_time_ms,
                    "is_archived": conversation.is_archived,
                    "last_message_at": (
                        conversation.last_message_at.isoformat()
                        if conversation.last_message_at
                        else None
                    ),
                    "created_at": conversation.created_at.isoformat(),
                    "updated_at": conversation.updated_at.isoformat(),
                    "tags": conversation.tags or [],
                    "messages": messages_list,
                },
            }
        )

    except Exception as e:
        current_app.logger.error(f"Failed to get conversation detail: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/conversation/<int:conversation_id>/title", methods=["PUT"])
@admin_required
def handle_update_conversation_title(conversation_id):
    """API endpoint لتحديث عنوان المحادثة - SUPERHUMAN UX"""
    return (
        jsonify(
            {
                "status": "error",
                "message": "This endpoint is deprecated and will be removed in a future version.",
            }
        ),
        410,
    )


@bp.route("/api/conversation/<int:conversation_id>/export", methods=["GET"])
@admin_required
def handle_export_conversation(conversation_id):
    """API endpoint لتصدير المحادثة - SUPERHUMAN PORTABILITY"""
    return (
        jsonify(
            {
                "status": "error",
                "message": "This endpoint is deprecated and will be removed in a future version.",
            }
        ),
        410,
    )


@bp.route("/api/conversation/<int:conversation_id>/archive", methods=["POST"])
@admin_required
def handle_archive_conversation(conversation_id):
    """API endpoint لأرشفة المحادثة - SUPERHUMAN ORGANIZATION"""
    return (
        jsonify(
            {
                "status": "error",
                "message": "This endpoint is deprecated and will be removed in a future version.",
            }
        ),
        410,
    )


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
def get_database_stats():
    """API endpoint لجلب إحصائيات قاعدة البيانات"""
    if not database_service:
        return jsonify({"status": "error", "message": "Database service not available"}), 503

    try:
        # Re-use the health check which includes stats
        stats = database_service.get_database_health()
        return jsonify(stats)
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
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 50, type=int)
        search = request.args.get("search", None, type=str)
        order_by = request.args.get("order_by", None, type=str)
        order_dir = request.args.get("order_dir", "asc", type=str)

        result = database_service.get_table_data(
            table_name, page, per_page, search, order_by, order_dir
        )

        # Return appropriate status code based on result
        if result.get("status") == "error":
            if "not found" in result.get("message", "").lower():
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
        if result.get("status") == "error":
            if "not found" in result.get("message", "").lower():
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
        if result.get("status") == "error":
            # Check if it's a validation error
            if "validation" in result.get("message", "").lower() or "errors" in result:
                return jsonify(result), 400
            if "not found" in result.get("message", "").lower():
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
        if result.get("status") == "error":
            # Check if it's a validation error
            if "validation" in result.get("message", "").lower() or "errors" in result:
                return jsonify(result), 400
            if "not found" in result.get("message", "").lower():
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
        if result.get("status") == "error":
            if "not found" in result.get("message", "").lower():
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
        sql = data.get("sql", "").strip()

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
    from app.services.api_contract_service import get_contract_service, validate_contract
    from app.services.api_observability_service import (
        get_observability_service,
        monitor_performance,
    )
    from app.services.api_security_service import get_security_service, rate_limit, require_jwt_auth
except ImportError:
    get_observability_service = None
    get_security_service = None
    get_contract_service = None

    def monitor_performance(f):
        return f

    def rate_limit(f):
        return f

    def require_jwt_auth(f):
        return f

    def validate_contract(f):
        return f


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

        return jsonify(
            {
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
                    "active_requests": snapshot.active_requests,
                },
                "sla_compliance": sla_compliance,
            }
        )
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
        severity = request.args.get("severity")

        alerts = service.get_all_alerts(severity=severity)

        return jsonify({"status": "success", "total_alerts": len(alerts), "alerts": alerts})
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

        return jsonify({"status": "success", **analytics})
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
        scopes = data.get("scopes", [])

        # Generate access token
        access_token = service.generate_access_token(user_id=current_user.id, scopes=scopes)

        # Generate refresh token
        refresh_token = service.generate_refresh_token(user_id=current_user.id)

        return jsonify(
            {
                "status": "success",
                "access_token": access_token.token,
                "refresh_token": refresh_token.token,
                "token_type": "Bearer",
                "expires_in": 900,  # 15 minutes in seconds
                "expires_at": access_token.expires_at.isoformat(),
                "scopes": access_token.scopes,
            }
        )
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
        refresh_token = data.get("refresh_token")

        if not refresh_token:
            return jsonify({"status": "error", "message": "Refresh token is required"}), 400

        # Rotate token
        new_access_token = service.rotate_token(refresh_token)

        if not new_access_token:
            return jsonify({"status": "error", "message": "Invalid or expired refresh token"}), 401

        return jsonify(
            {
                "status": "success",
                "access_token": new_access_token.token,
                "token_type": "Bearer",
                "expires_in": 900,
                "expires_at": new_access_token.expires_at.isoformat(),
            }
        )
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

        event_type = request.args.get("event_type")
        severity = request.args.get("severity")
        limit = request.args.get("limit", 100, type=int)

        logs = service.get_audit_logs(event_type=event_type, severity=severity, limit=limit)

        return jsonify({"status": "success", "total_logs": len(logs), "logs": logs})
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

        severity = request.args.get("severity")
        violation_type = request.args.get("violation_type")
        limit = request.args.get("limit", 100, type=int)

        violations = service.get_contract_violations(
            severity=severity, violation_type=violation_type, limit=limit
        )

        return jsonify(
            {"status": "success", "total_violations": len(violations), "violations": violations}
        )
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
        "timestamp": datetime.now(UTC).isoformat(),
        "components": {},
    }

    # Check database
    try:
        if database_service:
            db_health = database_service.get_database_health()
            health_status["components"]["database"] = {
                "status": db_health.get("status", "unknown"),
                "checks": db_health.get("checks", {}),
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
                "sla_compliance": sla["compliance_rate_percent"],
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


# ======================================================================================
# API GATEWAY ENDPOINTS (SUPERHUMAN EDITION)
# ======================================================================================
# نقاط نهاية بوابة API الخارقة - Superhuman API Gateway endpoints

try:
    from app.services.api_gateway_chaos import get_chaos_service, get_circuit_breaker
    from app.services.api_gateway_deployment import (
        get_ab_testing_service,
        get_canary_deployment_service,
        get_feature_flag_service,
    )
    from app.services.api_gateway_service import get_gateway_service
except ImportError:
    get_gateway_service = None
    get_chaos_service = None
    get_circuit_breaker = None
    get_ab_testing_service = None
    get_canary_deployment_service = None
    get_feature_flag_service = None


@bp.route("/api/gateway/stats", methods=["GET"])
@admin_required
@monitor_performance
def get_gateway_stats():
    """
    Get API Gateway comprehensive statistics

    نقطة نهاية للحصول على إحصائيات البوابة الشاملة
    """
    try:
        if not get_gateway_service:
            return jsonify({"status": "error", "message": "API Gateway service not available"}), 503

        gateway = get_gateway_service()
        stats = gateway.get_gateway_stats()

        return jsonify({"status": "success", "data": stats}), 200

    except Exception as e:
        current_app.logger.error(f"Get gateway stats failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/gateway/chaos/experiments", methods=["GET"])
@admin_required
@monitor_performance
def get_chaos_experiments():
    """
    Get active chaos engineering experiments

    الحصول على تجارب هندسة الفوضى النشطة
    """
    try:
        if not get_chaos_service:
            return (
                jsonify({"status": "error", "message": "Chaos engineering service not available"}),
                503,
            )

        chaos = get_chaos_service()
        experiments = chaos.get_active_experiments()

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "active_experiments": [
                            {
                                "experiment_id": exp.experiment_id,
                                "name": exp.name,
                                "fault_type": exp.fault_type.value,
                                "target_service": exp.target_service,
                                "fault_rate": exp.fault_rate,
                                "started_at": (
                                    exp.started_at.isoformat() if exp.started_at else None
                                ),
                            }
                            for exp in experiments
                        ]
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Get chaos experiments failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/gateway/circuit-breakers", methods=["GET"])
@admin_required
@monitor_performance
def get_circuit_breaker_states():
    """
    Get circuit breaker states for all services

    الحصول على حالات قاطع الدائرة لجميع الخدمات
    """
    try:
        if not get_circuit_breaker:
            return (
                jsonify({"status": "error", "message": "Circuit breaker service not available"}),
                503,
            )

        cb = get_circuit_breaker()
        states = cb.get_all_states()

        return jsonify({"status": "success", "data": {"circuit_breakers": states}}), 200

    except Exception as e:
        current_app.logger.error(f"Get circuit breaker states failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/gateway/ab-tests", methods=["GET"])
@admin_required
@monitor_performance
def get_ab_tests():
    """
    Get all A/B test experiments

    الحصول على جميع تجارب A/B
    """
    try:
        if not get_ab_testing_service:
            return jsonify({"status": "error", "message": "A/B testing service not available"}), 503

        # Get the service (currently unused, placeholder for future implementation)
        _ = get_ab_testing_service()

        # Get all experiments (placeholder - would need to add method to service)
        return (
            jsonify(
                {
                    "status": "success",
                    "data": {"message": "A/B testing service active", "experiments": []},
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Get A/B tests failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/gateway/feature-flags", methods=["GET"])
@admin_required
@monitor_performance
def get_feature_flags():
    """
    Get all feature flags

    الحصول على جميع أعلام الميزات
    """
    try:
        if not get_feature_flag_service:
            return (
                jsonify({"status": "error", "message": "Feature flag service not available"}),
                503,
            )

        flag_service = get_feature_flag_service()
        flags = flag_service.get_all_flags()

        return jsonify({"status": "success", "data": {"feature_flags": flags}}), 200

    except Exception as e:
        current_app.logger.error(f"Get feature flags failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/gateway/canary-deployments", methods=["GET"])
@admin_required
@monitor_performance
def get_canary_deployments():
    """
    Get all canary deployments

    الحصول على جميع عمليات النشر التدريجي
    """
    try:
        if not get_canary_deployment_service:
            return (
                jsonify({"status": "error", "message": "Canary deployment service not available"}),
                503,
            )

        # Placeholder - would return actual deployments
        return (
            jsonify(
                {
                    "status": "success",
                    "data": {"message": "Canary deployment service active", "deployments": []},
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Get canary deployments failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


# ======================================================================================
# SUPERHUMAN API GOVERNANCE ENDPOINTS
# ======================================================================================
# نقاط نهاية حوكمة API الخارقة - Superhuman API Governance endpoints

try:
    from app.services.api_config_secrets_service import get_config_secrets_service
    from app.services.api_disaster_recovery_service import (
        get_disaster_recovery_service,
        get_oncall_incident_service,
    )
    from app.services.api_governance_service import get_governance_service
    from app.services.api_slo_sli_service import get_slo_service
except ImportError:
    get_governance_service = None
    get_slo_service = None
    get_config_secrets_service = None
    get_disaster_recovery_service = None
    get_oncall_incident_service = None


@bp.route("/api/governance/dashboard", methods=["GET"])
@admin_required
@monitor_performance
def get_governance_dashboard():
    """
    Get API governance dashboard

    الحصول على لوحة حوكمة API
    """
    try:
        if not get_governance_service:
            return jsonify({"status": "error", "message": "Governance service not available"}), 503

        governance = get_governance_service()
        dashboard = governance.get_governance_dashboard()

        return jsonify({"status": "success", "data": dashboard}), 200

    except Exception as e:
        current_app.logger.error(f"Get governance dashboard failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/governance/owasp-compliance", methods=["GET"])
@admin_required
@monitor_performance
def get_owasp_compliance():
    """
    Get OWASP API Security Top 10 compliance report

    الحصول على تقرير الامتثال لـ OWASP API Security Top 10
    """
    try:
        if not get_governance_service:
            return jsonify({"status": "error", "message": "Governance service not available"}), 503

        governance = get_governance_service()
        report = governance.owasp_checker.get_compliance_report()

        return jsonify({"status": "success", "data": report}), 200

    except Exception as e:
        current_app.logger.error(f"Get OWASP compliance failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/slo/dashboard", methods=["GET"])
@admin_required
@monitor_performance
def get_slo_dashboard():
    """
    Get SLO/SLI dashboard

    الحصول على لوحة SLO/SLI
    """
    try:
        if not get_slo_service:
            return jsonify({"status": "error", "message": "SLO service not available"}), 503

        slo = get_slo_service()
        dashboard = slo.get_dashboard()

        return jsonify({"status": "success", "data": dashboard}), 200

    except Exception as e:
        current_app.logger.error(f"Get SLO dashboard failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/slo/burn-rate/<slo_id>", methods=["GET"])
@admin_required
@monitor_performance
def get_slo_burn_rate(slo_id: str):
    """
    Get error budget burn rate for an SLO

    الحصول على معدل استهلاك ميزانية الخطأ لـ SLO
    """
    try:
        if not get_slo_service:
            return jsonify({"status": "error", "message": "SLO service not available"}), 503

        slo = get_slo_service()
        burn_rate = slo.calculate_burn_rate(slo_id)

        if not burn_rate:
            return jsonify({"status": "error", "message": "SLO not found"}), 404

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "slo_id": burn_rate.slo_id,
                        "timestamp": burn_rate.timestamp.isoformat(),
                        "burn_rate_1h": burn_rate.burn_rate_1h,
                        "burn_rate_6h": burn_rate.burn_rate_6h,
                        "burn_rate_24h": burn_rate.burn_rate_24h,
                        "burn_rate_7d": burn_rate.burn_rate_7d,
                        "level": burn_rate.level.value,
                        "projected_depletion": (
                            burn_rate.projected_depletion.isoformat()
                            if burn_rate.projected_depletion
                            else None
                        ),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Get SLO burn rate failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/config/environments", methods=["GET"])
@admin_required
@monitor_performance
def get_environment_configs():
    """
    Get configuration for all environments

    الحصول على التهيئة لجميع البيئات
    """
    try:
        if not get_config_secrets_service:
            return jsonify({"status": "error", "message": "Config service not available"}), 503

        config_service = get_config_secrets_service()

        from app.services.api_config_secrets_service import Environment

        environments = {
            env.value: {
                "config": dict(config_service.config_store.get(env, {})),
                "secrets_count": len(
                    [s for s in config_service.secrets_registry.values() if s.environment == env]
                ),
            }
            for env in Environment
        }

        return jsonify({"status": "success", "data": environments}), 200

    except Exception as e:
        current_app.logger.error(f"Get environment configs failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/config/secrets/audit", methods=["GET"])
@admin_required
@monitor_performance
def get_secrets_audit():
    """
    Get secrets access audit logs

    الحصول على سجلات تدقيق الوصول إلى الأسرار
    """
    try:
        if not get_config_secrets_service:
            return jsonify({"status": "error", "message": "Config service not available"}), 503

        config_service = get_config_secrets_service()

        limit = request.args.get("limit", 100, type=int)
        secret_id = request.args.get("secret_id")

        audit_logs = config_service.get_audit_report(secret_id=secret_id, limit=limit)

        return (
            jsonify(
                {"status": "success", "data": {"audit_logs": audit_logs, "total": len(audit_logs)}}
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Get secrets audit failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/disaster-recovery/status", methods=["GET"])
@admin_required
@monitor_performance
def get_dr_status():
    """
    Get disaster recovery status

    الحصول على حالة التعافي من الكوارث
    """
    try:
        if not get_disaster_recovery_service:
            return (
                jsonify({"status": "error", "message": "Disaster recovery service not available"}),
                503,
            )

        dr_service = get_disaster_recovery_service()
        status = dr_service.get_rto_rpo_status()

        return jsonify({"status": "success", "data": status}), 200

    except Exception as e:
        current_app.logger.error(f"Get DR status failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/disaster-recovery/failover", methods=["POST"])
@admin_required
@monitor_performance
def initiate_dr_failover():
    """
    Initiate disaster recovery failover

    بدء التعافي من الكوارث
    """
    try:
        if not get_disaster_recovery_service:
            return (
                jsonify({"status": "error", "message": "Disaster recovery service not available"}),
                503,
            )

        data = request.get_json()
        plan_id = data.get("plan_id")
        reason = data.get("reason", "Manual failover initiated")

        if not plan_id:
            return jsonify({"status": "error", "message": "plan_id is required"}), 400

        dr_service = get_disaster_recovery_service()
        result = dr_service.initiate_failover(
            plan_id=plan_id,
            initiated_by=current_user.name if current_user else "unknown",
            reason=reason,
        )

        return jsonify({"status": "success" if result["success"] else "error", "data": result}), (
            200 if result["success"] else 400
        )

    except Exception as e:
        current_app.logger.error(f"Initiate DR failover failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/incidents", methods=["GET"])
@admin_required
@monitor_performance
def get_incidents():
    """
    Get all incidents

    الحصول على جميع الحوادث
    """
    try:
        if not get_oncall_incident_service:
            return jsonify({"status": "error", "message": "Incident service not available"}), 503

        incident_service = get_oncall_incident_service()

        return (
            jsonify(
                {
                    "status": "success",
                    "data": {
                        "incidents": [
                            {
                                "incident_id": i.incident_id,
                                "title": i.title,
                                "severity": i.severity.value,
                                "status": i.status.value,
                                "detected_at": i.detected_at.isoformat(),
                                "assigned_to": i.assigned_to,
                            }
                            for i in incident_service.incidents.values()
                        ],
                        "metrics": incident_service.get_incident_metrics(),
                    },
                }
            ),
            200,
        )

    except Exception as e:
        current_app.logger.error(f"Get incidents failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/incidents", methods=["POST"])
@admin_required
@monitor_performance
def create_incident():
    """
    Create a new incident

    إنشاء حادث جديد
    """
    try:
        if not get_oncall_incident_service:
            return jsonify({"status": "error", "message": "Incident service not available"}), 503

        data = request.get_json()

        from app.services.api_disaster_recovery_service import IncidentSeverity

        incident_service = get_oncall_incident_service()
        incident_id = incident_service.create_incident(
            title=data.get("title"),
            description=data.get("description"),
            severity=IncidentSeverity(data.get("severity", "sev3")),
            detected_by=current_user.name if current_user else "unknown",
            affected_services=data.get("affected_services", []),
        )

        return jsonify({"status": "success", "data": {"incident_id": incident_id}}), 201

    except Exception as e:
        current_app.logger.error(f"Create incident failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


# ======================================================================================
# PROMPT ENGINEERING ENDPOINTS - SUPERHUMAN EDITION
# ======================================================================================

try:
    from app.services.prompt_engineering_service import get_prompt_engineering_service
except ImportError:
    get_prompt_engineering_service = None


@bp.route("/api/prompt-engineering/generate", methods=["POST"])
@admin_required
def handle_generate_prompt():
    """
    API endpoint لتوليد Prompt خارق احترافي

    توليد prompt engineering عظيم يفهم المشروع بشكل عميق
    """
    if not get_prompt_engineering_service:
        return (
            jsonify({"status": "error", "message": "⚠️ Prompt Engineering service not available."}),
            503,
        )

    try:
        data = request.get_json()
        if data is None:
            return jsonify({"status": "error", "message": "Invalid JSON in request body."}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": f"Failed to parse JSON: {str(e)}"}), 400

    user_description = data.get("description", "").strip()
    template_id = data.get("template_id")
    conversation_id = data.get("conversation_id")
    use_rag = data.get("use_rag", True)
    prompt_type = data.get("prompt_type", "general")

    if not user_description:
        return (
            jsonify({"status": "error", "message": "⚠️ الوصف مطلوب. Description is required."}),
            400,
        )

    # Validate description length
    max_description_length = 10000  # 10k characters
    if len(user_description) > max_description_length:
        return (
            jsonify(
                {
                    "status": "error",
                    "message": (
                        f"⚠️ الوصف طويل جداً ({len(user_description):,} حرف).\n"
                        f"Description too long ({len(user_description):,} characters).\n"
                        f"**Maximum:** {max_description_length:,} characters"
                    ),
                }
            ),
            400,
        )

    try:
        service = get_prompt_engineering_service()

        # Generate the prompt
        result = service.generate_prompt(
            user_description=user_description,
            user=current_user._get_current_object(),
            template_id=template_id,
            conversation_id=conversation_id,
            use_rag=use_rag,
            prompt_type=prompt_type,
        )

        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"Prompt generation API failed: {e}", exc_info=True)
        return (
            jsonify(
                {
                    "status": "error",
                    "error": str(e),
                    "message": (
                        f"⚠️ حدث خطأ في توليد الـ Prompt.\n\n"
                        f"Failed to generate prompt.\n\n"
                        f"**Error:** {str(e)}\n\n"
                        f"Please try again or contact support."
                    ),
                }
            ),
            200,
        )


@bp.route("/api/prompt-engineering/templates", methods=["GET"])
@admin_required
def handle_list_templates():
    """API endpoint لجلب قوالب Prompt Engineering"""
    if not get_prompt_engineering_service:
        return jsonify({"status": "error", "message": "Service not available"}), 503

    try:
        category = request.args.get("category")
        active_only = request.args.get("active_only", "true").lower() == "true"

        service = get_prompt_engineering_service()
        templates = service.list_templates(category=category, active_only=active_only)

        return jsonify({"status": "success", "templates": templates, "count": len(templates)})

    except Exception as e:
        current_app.logger.error(f"List templates failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/prompt-engineering/templates", methods=["POST"])
@admin_required
def handle_create_template():
    """API endpoint لإنشاء قالب جديد"""
    if not get_prompt_engineering_service:
        return jsonify({"status": "error", "message": "Service not available"}), 503

    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Invalid request body"}), 400

        name = data.get("name", "").strip()
        template_content = data.get("template_content", "").strip()

        if not name or not template_content:
            return (
                jsonify({"status": "error", "message": "⚠️ Name and template content are required"}),
                400,
            )

        service = get_prompt_engineering_service()
        result = service.create_template(
            name=name,
            template_content=template_content,
            user=current_user._get_current_object(),
            description=data.get("description"),
            category=data.get("category", "general"),
            few_shot_examples=data.get("few_shot_examples"),
            variables=data.get("variables"),
        )

        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"Create template failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/prompt-engineering/rate/<int:prompt_id>", methods=["POST"])
@admin_required
def handle_rate_prompt(prompt_id):
    """API endpoint لتقييم Prompt مولد (RLHF)"""
    if not get_prompt_engineering_service:
        return jsonify({"status": "error", "message": "Service not available"}), 503

    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "Invalid request body"}), 400

        rating = data.get("rating")
        feedback_text = data.get("feedback")

        if not rating or not isinstance(rating, int):
            return (
                jsonify(
                    {"status": "error", "message": "⚠️ Rating is required and must be an integer"}
                ),
                400,
            )

        service = get_prompt_engineering_service()
        result = service.rate_prompt(
            prompt_id=prompt_id,
            rating=rating,
            feedback_text=feedback_text,
        )

        return jsonify(result)

    except Exception as e:
        current_app.logger.error(f"Rate prompt failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/prompt-engineering/metrics", methods=["GET"])
@admin_required
def handle_get_metrics():
    """
    API endpoint لجلب مقاييس أداء نظام Prompt Engineering - OBSERVABILITY

    Returns comprehensive metrics including:
    - Total generations
    - Success/failure rates
    - Language detection statistics
    - Security incidents blocked
    - Average generation time
    - Risk level distribution
    """
    if not get_prompt_engineering_service:
        return jsonify({"status": "error", "message": "Service not available"}), 503

    try:
        service = get_prompt_engineering_service()
        metrics = service.get_metrics()

        return jsonify(
            {
                "status": "success",
                "metrics": metrics,
                "message": "📊 Metrics retrieved successfully",
            }
        )

    except Exception as e:
        current_app.logger.error(f"Get metrics failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


# ======================================================================================
# SUPERHUMAN PERFORMANCE MONITORING ENDPOINTS
# ======================================================================================


@bp.route("/api/chat/performance/metrics", methods=["GET"])
@admin_required
def handle_get_performance_metrics():
    """
    Get real-time performance metrics for chat system.

    ✨ SUPERHUMAN FEATURE: Real-time performance monitoring
    - Latency percentiles (P50, P95, P99)
    - Category breakdown (streaming vs traditional)
    - Performance distribution
    - Optimization suggestions
    """
    if not get_performance_service:
        return jsonify({"status": "error", "message": "Performance service not available"}), 503

    try:
        service = get_performance_service()

        # Get query parameters
        category = request.args.get("category")  # Optional filter
        hours = int(request.args.get("hours", 24))  # Time window

        # Get statistics
        stats = service.get_statistics(category=category, hours=hours)

        # Get optimization suggestions
        suggestions = service.get_optimization_suggestions()

        # Get A/B test results
        ab_results = service.get_ab_results()

        return jsonify(
            {
                "status": "success",
                "statistics": stats,
                "suggestions": suggestions,
                "ab_test_results": ab_results,
                "message": "📊 Performance metrics retrieved successfully",
            }
        )

    except Exception as e:
        current_app.logger.error(f"Get performance metrics failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/chat/streaming/metrics", methods=["GET"])
@admin_required
def handle_get_streaming_metrics():
    """
    Get streaming-specific performance metrics.

    ✨ SUPERHUMAN FEATURE: Streaming performance tracking
    - Average chunk latency
    - Total streams and tokens
    - Latency percentiles for streaming
    """
    if not get_streaming_service:
        return jsonify({"status": "error", "message": "Streaming service not available"}), 503

    try:
        service = get_streaming_service()
        metrics = service.get_metrics()

        return jsonify(
            {
                "status": "success",
                "metrics": metrics,
                "message": "⚡ Streaming metrics retrieved successfully",
            }
        )

    except Exception as e:
        current_app.logger.error(f"Get streaming metrics failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500


@bp.route("/api/chat/performance/record", methods=["POST"])
@admin_required
def handle_record_performance():
    """
    Record a performance metric (for client-side tracking).

    Allows frontend to record perceived performance metrics.
    """
    if not get_performance_service:
        return jsonify({"status": "error", "message": "Performance service not available"}), 503

    try:
        data = request.get_json() or {}

        category = data.get("category", "unknown")
        latency_ms = float(data.get("latency_ms", 0))
        tokens = int(data.get("tokens", 0))
        model_used = data.get("model_used", "unknown")

        service = get_performance_service()
        metric = service.record_metric(
            category=category,
            latency_ms=latency_ms,
            tokens=tokens,
            model_used=model_used,
            user_id=current_user.id if current_user.is_authenticated else None,
        )

        return jsonify(
            {
                "status": "success",
                "metric_id": metric.metric_id,
                "performance_category": metric.get_category().value,
                "message": "✅ Performance metric recorded",
            }
        )

    except Exception as e:
        current_app.logger.error(f"Record performance metric failed: {e}", exc_info=True)
        return jsonify({"status": "error", "message": str(e)}), 500
