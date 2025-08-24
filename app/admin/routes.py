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