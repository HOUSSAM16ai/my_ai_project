# app/admin/__init__.py
# ======================================================================================
# ==                      ADMINISTRATIVE BLUEPRINT CONSTITUTION                       ==
# ======================================================================================
# PRIME DIRECTIVE:
#   This file defines the 'admin' blueprint, the self-contained administrative
#   module of the application.
#
# ARCHITECTURAL FIX (v2.0):
#   - Added `template_folder='templates'` to correctly scope the template lookups
#     for this blueprint, resolving all `TemplateNotFound` errors for admin pages.

from flask import Blueprint, jsonify

# We explicitly declare that this blueprint's templates reside in a subfolder
# named 'templates' relative to this __init__.py file.
bp = Blueprint("admin", __name__, template_folder="templates")


# Global error handler for the admin blueprint to ensure JSON responses for API endpoints
@bp.errorhandler(Exception)
def handle_error(error):
    """Global error handler for admin blueprint - ensures JSON responses for API calls"""
    from flask import request

    # Only return JSON errors for API endpoints
    if request.path.startswith("/admin/api/"):
        return jsonify({"status": "error", "message": str(error)}), 500

    # For non-API routes, re-raise the error to be handled by Flask's default handler
    raise error


# Import the routes *after* the blueprint is defined to avoid circular dependencies.
from app.admin import routes
