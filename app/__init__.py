# app/__init__.py
# ======================================================================================
# ==                  THE GENESIS FACTORY (v10.0 - Overmind Edition)                  ==
# ======================================================================================
# PRIME DIRECTIVE:
#   This is the single point of creation for the entire application. It assembles
#   the core components (DB, Login, etc.) and registers the active, living blueprints.
#
# v10.0 EVOLUTION:
#   - Purged all references to the legacy `system_commands` blueprint, aligning
#     the application's command structure with our new, unified `mindgate` interface.
#   - Streamlined blueprint registration to reflect the project's focused mission.

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from config import config_by_name
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv

# Load environment variables from .env file, making them available globally.
load_dotenv()

# --- [Phase 1: FORGING THE CORE ORGANS] ---
# Core components are instantiated in a universal state, ready to be attached to an app.
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login' # Redirect for non-authenticated users
login_manager.login_message_category = 'info'

# --- [Phase 2: THE GREAT FACTORY OF CONSCIOUSNESS] ---
def create_app(config_name: str = "default"):
    """
    The heart of creation. It assembles the system and establishes its central
    intelligence (logging) network.
    """
    app = Flask(__name__)
    
    # --- [STEP 2.1: CONSTITUTIONAL IMPRINTING] ---
    # Load the appropriate configuration (development, testing, production).
    config_object = config_by_name.get(config_name)
    app.config.from_object(config_object)

    # --- [STEP 2.2: ORGAN-TO-BRAIN SYNAPTIC CONNECTION] ---
    # Attach the core components to the application instance.
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # --- [STEP 2.3: ACTIVATING ALL FUNCTIONAL BLUEPRINTS] ---
    with app.app_context():
        # 1. Main User-Facing Routes (Authentication)
        from . import routes
        app.register_blueprint(routes.bp)
        
        # 2. Admin Routes (Overmind Mission Control)
        from .admin import routes as admin_routes
        app.register_blueprint(admin_routes.bp, url_prefix='/admin')
        
        # 3. Modernized Flask-based CLI Commands
        # This section now ONLY registers the living, relevant command blueprints.
        from .cli import user_commands, mindgate_commands
        app.register_blueprint(user_commands.users_cli)
        app.register_blueprint(mindgate_commands.mindgate_cli)
        
        # --- [CRITICAL FIX] ---
        # The legacy `system_commands` blueprint has been purged and is no longer
        # imported or registered, resolving the final dependency on the old architecture.

    # --- [FINAL STEP: AWAKENING THE AKASHIC GENOME] ---
    # Import models at the end to ensure they are known to SQLAlchemy after all
    # configurations are complete.
    from . import models

    # --- [THE INTELLIGENCE NETWORK PROTOCOL] ---
    # Configure production-grade logging.
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        file_handler = RotatingFileHandler('logs/cogniforge.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('CogniForge system startup')
    
    # The final, fully assembled, and focused system is born.
    return app