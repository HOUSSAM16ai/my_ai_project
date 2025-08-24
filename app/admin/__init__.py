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

from flask import Blueprint

# We explicitly declare that this blueprint's templates reside in a subfolder
# named 'templates' relative to this __init__.py file.
bp = Blueprint(
    'admin',
    __name__,
    template_folder='templates'
)

# Import the routes *after* the blueprint is defined to avoid circular dependencies.
from app.admin import routes