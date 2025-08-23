# app/routes.py
# ======================================================================================
# ==                      THE OVERMIND USER GATEWAY (v4.0)                            ==
# ======================================================================================
# PRIME DIRECTIVE:
#   This blueprint manages the primary, user-facing entry points of the application.
#   It is now streamlined to focus exclusively on core functionalities:
#   user authentication and providing the primary dashboard interface.
#
#   All legacy educational routes (`/subjects`, `/lessons`, etc.) have been
#   surgically removed to align with the project's strategic focus on the
#   Overmind agent architecture.
#
# ARCHITECTURAL NOTES:
#   - User management remains critical for identifying initiators of Missions.
#   - The dashboard route will serve as the future entry point for interacting
#     with Mission control panels.

from flask import render_template, flash, redirect, url_for, Blueprint
from flask_login import current_user, login_user, logout_user, login_required

from app import db
# (الحل) قمنا بتطهير الاستيرادات.
# `SubmissionForm` لم يعد مطلوبًا هنا.
from app.forms import LoginForm, RegistrationForm
# (الحل) نستورد فقط النماذج التي نستخدمها بالفعل.
from app.models import User

# Create a self-contained unit of routes named 'main'.
bp = Blueprint('main', __name__)

# --- Core Application Routes ---

@bp.route('/')
@bp.route('/home')
def home():
    """
    Serves the main landing page.
    """
    return render_template('home.html', title='Home')

@bp.route('/dashboard')
@login_required
def dashboard():
    """
    Serves the primary user dashboard. This is the protected area for authenticated users
    and will be the future home for mission control interfaces.
    """
    # NOTE: In the future, we will pass mission data, etc., to this template.
    return render_template('dashboard.html', title='Dashboard')

# --- User Authentication Routes (CRITICAL & RETAINED) ---

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handles new user registration.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(full_name=form.full_name.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('main.login'))
        
    return render_template('register.html', title='Register', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Handles user login.
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Login Unsuccessful. Please check email and password.', 'danger')
            return redirect(url_for('main.login'))
            
        login_user(user)
        # In the future, redirect to the admin dashboard if the user is an admin.
        redirect_url = url_for('admin.admin_dashboard') if user.is_admin else url_for('main.dashboard')
        return redirect(redirect_url)

    return render_template('login.html', title='Login', form=form)

@bp.route('/logout')
@login_required
def logout():
    """
    Handles user logout.
    """
    logout_user()
    return redirect(url_for('main.home'))

# --- LEGACY EDUCATIONAL ROUTES (PURGED) ---
#
# The routes for /subjects, /lessons, and /exercise have been removed as they
# relied on models that are no longer part of the core "Akashic Genome".
# This aligns the application's surface with its new strategic mission.
#