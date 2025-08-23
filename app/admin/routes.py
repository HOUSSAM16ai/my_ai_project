# app/admin/routes.py
# ======================================================================================
# ==                        OVERMIND MISSION CONTROL (v10.0)                          ==
# ======================================================================================
# PRIME DIRECTIVE:
#   This blueprint serves as the primary command & control interface for the Overmind
#   and Maestro systems. It has been re-architected to be Mission-centric,
#   replacing the legacy Conversation-based model.
#
#   It provides the administrative surface for initiating, monitoring, and analyzing
#   strategic AI missions.

from flask import render_template, abort, request, jsonify, flash, current_app
from flask_login import current_user, login_required
from functools import wraps

from app.admin import bp
from app import db

# --- [THE NEW REALITY] ---
# We now import the models that define our new strategic architecture.
from app.models import User, Mission, Task

# --- [THE STRATEGIC ORCHESTRATORS] ---
# We import the high-level services that drive the AI's actions.
from app.services import generation_service as maestro
from app.services import master_agent_service as overmind

# --------------------------------------------------------------------------------------
# Authentication & Authorization
# --------------------------------------------------------------------------------------

def admin_required(f):
    """Decorator to ensure the user is logged in and is an administrator."""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            # Forbid access for non-admin users.
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# --------------------------------------------------------------------------------------
# Mission Control Routes
# --------------------------------------------------------------------------------------

@bp.route("/dashboard")
@admin_required
def admin_dashboard():
    """
    Displays the main admin command center, showing a list of all active and
    past missions.
    """
    try:
        # The dashboard is now a mission roster.
        missions = Mission.query.order_by(Mission.updated_at.desc()).all()
    except Exception as e:
        current_app.logger.error(f"Failed to fetch missions for dashboard: {e}", exc_info=True)
        flash("Could not retrieve mission list from the Akashic Records.", "danger")
        missions = []

    return render_template(
        "admin/admin_dashboard.html", # Assuming template is in app/admin/templates
        title="Overmind Mission Control",
        missions=missions
    )

@bp.route("/mission/<int:mission_id>")
@admin_required
def mission_detail(mission_id):
    """
    Displays the detailed view of a single mission, including its objective,
    status, plan, and all associated tasks and events.
    """
    mission = Mission.query.get_or_404(mission_id)
    # This will be used to render the full mission log in the template.
    return render_template("admin/mission_detail.html", title=f"Mission #{mission.id}", mission=mission)

# --------------------------------------------------------------------------------------
# API Gateways (The Conduits to the AI Minds)
# --------------------------------------------------------------------------------------

@bp.route("/api/start-mission", methods=["POST"])
@admin_required
def handle_start_mission():
    """
    API Gateway to the Overmind. Receives a high-level objective and initiates
    a new strategic mission.
    """
    data = request.json
    objective = data.get("objective")

    if not objective:
        return jsonify({"status": "error", "message": "Objective is required."}), 400

    try:
        current_app.logger.info(f"API: Received objective '{objective}' from user {current_user.id}.")
        # Engage the Overmind to start the mission.
        # The Overmind service handles all the complex logic internally.
        mission = overmind.start_mission(objective=objective, initiator=current_user)
        return jsonify({
            "status": "success",
            "message": "Mission initiated successfully.",
            "mission_id": mission.id,
            "redirect_url": url_for('admin.mission_detail', mission_id=mission.id)
        })
    except Exception as e:
        current_app.logger.error(f"Failed to start mission via API: {e}", exc_info=True)
        return jsonify({"status": "error", "message": f"Failed to start mission: {e}"}), 500


@bp.route("/api/maestro-chat", methods=["POST"])
@admin_required
def handle_maestro_chat():
    """
    API Gateway to the Maestro. This provides a direct, tactical chat interface
    for quick tasks, debugging, or direct interaction, bypassing the Overmind's
    strategic layer. It now requires a conversation_id.
    """
    data = request.json
    prompt = data.get("prompt")
    conversation_id = data.get("conversation_id") # Must be provided by the front-end
    history = data.get("history", [])

    if not prompt:
        return jsonify({"status": "error", "message": "Prompt is required."}), 400
    if not conversation_id:
        return jsonify({"status": "error", "message": "Conversation ID is required for Maestro chat."}), 400
    
    # Engage the Maestro tactical engine directly.
    result = maestro.forge_new_code(
        prompt=prompt,
        conversation_history=history,
        conversation_id=conversation_id
    )
    return jsonify(result)

# --------------------------------------------------------------------------------------
# Administrative Utility Routes
# --------------------------------------------------------------------------------------

@bp.route("/users")
@admin_required
def list_users():
    """
    Displays a list of all users in the system. (Functionality retained).
    """
    try:
        all_users = db.session.scalars(db.select(User).order_by(User.id)).all()
    except Exception as e:
        flash(f"Error fetching users: {e}", "danger")
        all_users = []

    return render_template("admin/admin_users.html", title="User Roster", users=all_users)