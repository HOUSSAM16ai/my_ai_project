# app/admin/routes.py - The Immortal Memory Commander (v7.1 - Final & Hardened)

from flask import render_template, abort, request, jsonify, flash, current_app # <-- [THE ULTIMATE FIX]
from flask_login import current_user, login_required
from functools import wraps

from app.admin import bp
from app.models import User, Conversation
from app import db
from app.services.generation_service import forge_new_code


# --- [THE UNIFIED AUTHENTICATION PROTOCOL] ---
# This decorator remains the gold standard for securing our admin routes.
def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


# --- The Dashboard, now the starting point of every immortal conversation ---
@bp.route("/dashboard")
@admin_required
def dashboard():
    """
    Displays the main admin command center and INITIATES a new immortal conversation.
    """
    conversation_id = None # Initialize to None for safety
    try:
        # --- [IMMORTAL MEMORY PROTOCOL - STEP 1: INITIATION] ---
        new_conversation = Conversation(user_id=current_user.id)
        db.session.add(new_conversation)
        db.session.commit()
        conversation_id = new_conversation.id
        
        # Now that current_app is imported, this will work perfectly.
        current_app.logger.info(f"New conversation '{conversation_id}' started for user '{current_user.email}'")
    
    except Exception as e:
        db.session.rollback()
        # Log the error even if the page loads, so we know something went wrong.
        current_app.logger.error(f"Failed to create new conversation for user '{current_user.email}': {e}", exc_info=True)
        flash("Could not initialize a new conversation session. History will not be saved.", "danger")

    return render_template(
        "admin_dashboard.html",
        title="Admin Command Center",
        conversation_id=conversation_id
    )


# --- The API, now aware of the ongoing conversation's identity ---
@bp.route("/api/generate-code", methods=["POST"])
@admin_required
def handle_generate_code_from_ui():
    """
    The secure API gateway that now receives the conversation context
    and passes it to the AI's synthesizing core.
    """
    data = request.json
    prompt = data.get("prompt")
    conversation_id = data.get("conversation_id")
    history = data.get("history", [])

    if not prompt:
        return jsonify({"status": "error", "message": "Prompt is required."}), 400
    if not conversation_id:
        current_app.logger.warning("API call received without a conversation_id.")
        return jsonify({"status": "error", "message": "Conversation ID is missing. Please refresh the page."}), 400

    result = forge_new_code(
        prompt=prompt,
        conversation_history=history,
        conversation_id=conversation_id
    )
    return jsonify(result)


# --- Example of other admin routes, also protected ---
@bp.route("/users")
@admin_required
def list_users():
    """
    Displays a list of all users in the system.
    """
    try:
        all_users = db.session.scalars(db.select(User).order_by(User.id)).all()
    except Exception as e:
        flash(f"Error fetching users: {e}", "danger")
        all_users = []

    return render_template("admin_users.html", title="User Roster", users=all_users)
