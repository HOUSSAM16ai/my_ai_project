# app/extensions.py
"""Centralized extension management to avoid circular imports."""

from flask import jsonify, redirect, request, url_for
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "main.login"
login_manager.login_message_category = "info"


def custom_unauthorized_handler():
    """
    Redirects to the login page for unauthorized web requests, but returns a
    JSON 401 error for unauthorized API requests. This prevents breaking SSE
    connections which expect an event-stream response, not an HTML redirect.
    """
    # Check if the request path is for an API endpoint
    if request.path.startswith("/api/"):
        return jsonify(error="Unauthorized"), 401
    # For all other unauthorized requests, redirect to the login page
    return redirect(url_for("main.login"))


login_manager.unauthorized_handler(custom_unauthorized_handler)
