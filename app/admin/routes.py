# app/admin/routes.py - The Absolute Commander v4.0

from flask import render_template, abort
from flask_login import current_user, login_required

from app.admin import bp
from app.models import User # <-- He talks to HIS OWN models
from app import db # <-- He uses HIS OWN database connection

@bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.email != "benmerahhoussam16@gmail.com":
        abort(403)

    user_count = "N/A"
    all_users = []
    error_message = None

    try:
        # --- THE SUPERCHARGED FIX: We query our OWN database directly ---
        user_count = db.session.query(User).count()
        all_users = db.session.query(User).order_by(User.id).all()

    except Exception as e:
        error_message = f"FATAL: Could not query local database: {e}"
        flash(error_message, 'danger')

    return render_template(
        'admin_dashboard.html', 
        title='Admin Command Center', 
        user_count=user_count,
        all_users=all_users,
        error_message=error_message
    )