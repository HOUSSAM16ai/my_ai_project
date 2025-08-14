# app/admin/routes.py - The Absolute Commander v6.0 (The Unified Protocol)

from flask import render_template, abort, request, jsonify, flash
from flask_login import current_user, login_required
from functools import wraps  # <-- استيراد ضروري للمزخرف

from app.admin import bp
from app.models import User
from app import db
from app.services.generation_service import forge_new_code


# --- [THE UNIFIED AUTHENTICATION PROTOCOL] ---
# We create a simple decorator to check for admin status.
# This avoids code repetition and creates a single source of truth for admin access.
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)  # Access Forbidden
        return f(*args, **kwargs)

    return decorated_function


# --- نهاية البروتوكول ---


# --- The Dashboard, now protected by the unified protocol ---
@bp.route("/dashboard")
@admin_required  # <-- استخدام البروتوكول الجديد
def dashboard():
    """
    Displays the main admin command center, now protected by the unified admin check.
    """
    return render_template("admin_dashboard.html", title="Admin Command Center")


# --- The API for the UI, also protected by the unified protocol ---
@bp.route("/api/generate-code", methods=["POST"])
@admin_required  # <-- استخدام نفس البروتوكول
def handle_generate_code_from_ui():
    """
    The secure API gateway for the AI Command Console.
    """
    prompt = request.json.get("prompt")
    if not prompt:
        return jsonify({"status": "error", "message": "Prompt is required."}), 400

    result = forge_new_code(prompt)
    return jsonify(result)


# --- Example of other admin routes, also protected ---
@bp.route("/users")
@admin_required  # <-- استخدام نفس البروتوكول
def list_users():
    """
    Displays a list of all users in the system.
    """
    try:
        # Use the modern, recommended way to query
        all_users = db.session.scalars(db.select(User).order_by(User.id)).all()
    except Exception as e:
        flash(f"Error fetching users: {e}", "danger")
        all_users = []

    return render_template("admin_users.html", title="User Roster", users=all_users)
