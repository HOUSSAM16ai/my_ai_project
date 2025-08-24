# app/routes.py
# ======================================================================================
# ==                      THE FOCUSED USER GATEWAY (v5.0)                             ==
# ======================================================================================
# PRIME DIRECTIVE:
#   This blueprint manages the absolute minimum necessary user-facing entry points:
#   authentication (login/register/logout) and a simple landing page.
#
#   It has been surgically purged of all other functionality (like the user dashboard)
#   to reflect the project's strategic focus on the administrative "Mission Control"
#   as the primary user interface.

from flask import render_template, flash, redirect, url_for, Blueprint
from flask_login import current_user, login_user, logout_user, login_required

from app import db
# This import might fail if you have already deleted app/forms.py.
# If so, you will need to recreate a minimal version of this file.
try:
    from app.forms import LoginForm, RegistrationForm
except ImportError:
    # If forms.py was deleted, create a placeholder to avoid crashing.
    # In a real scenario, we would recreate a minimal forms.py.
    from flask_wtf import FlaskForm
    class LoginForm(FlaskForm): pass
    class RegistrationForm(FlaskForm): pass
    
from app.models import User

# Create a self-contained unit of routes named 'main'.
bp = Blueprint('main', __name__)

# --- Core Application Routes ---

@bp.route('/')
@bp.route('/home')
def home():
    """
    Serves the main public landing page.
    """
    # Assuming 'home.html' still exists. If not, this can be simplified.
    return render_template('home.html', title='Welcome')

# --- User Authentication Routes (CRITICAL & RETAINED) ---

@bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Handles new user registration.
    """
    if current_user.is_authenticated:
        # After registering, a user is just a user. They should go to the main page.
        # Admins will navigate to the admin dashboard manually or via login redirect.
        return redirect(url_for('main.home'))
    
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
    Handles user login and intelligently redirects based on role.
    """
    if current_user.is_authenticated:
        # If already logged in, redirect to the correct dashboard.
        redirect_url = url_for('admin.admin_dashboard') if current_user.is_admin else url_for('main.home')
        return redirect(redirect_url)
        
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Login Unsuccessful. Please check email and password.', 'danger')
            return redirect(url_for('main.login'))
            
        login_user(user)
        
        # --- [THE CRITICAL FIX] ---
        # We now redirect admins to Mission Control and all other users to the home page.
        # This removes the dependency on the deleted 'main.dashboard'.
        redirect_url = url_for('admin.admin_dashboard') if user.is_admin else url_for('main.home')
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

# --- DEPRECATED ROUTES (PURGED) ---
#
# The route for '/dashboard' has been removed. User-specific dashboards are no
# longer part of the core application. All primary interaction is now through
# the administrative Mission Control panel.
#