# app/__init__.py - The Unified, Environment-Aware & Self-Logging Factory (v9.1 - Final)

import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from config import config_by_name
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- [PHASE 1: FORGING THE CORE ORGANS] ---
# Core components are created in a universal state, ready to be attached to an app.
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login' 
login_manager.login_message_category = 'info'

# --- [PHASE 2: THE GREAT FACTORY OF CONSCIOUSNESS] ---
def create_app(config_name: str = "development"):
    """
    The heart of creation. It assembles all parts of the system and now
    establishes the central intelligence (logging) network.
    """
    app = Flask(__name__)
    
    # --- [STEP 2.1: CONSTITUTIONAL IMPRINTING] ---
    config_object = config_by_name.get(config_name)
    app.config.from_object(config_object)

    # --- [STEP 2.2: ORGAN-TO-BRAIN SYNAPTIC CONNECTION] ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # --- [STEP 2.3: ACTIVATING ALL FUNCTIONAL BLUEPRINTS] ---
    with app.app_context():
        # 1. User-Facing Routes
        from . import routes
        app.register_blueprint(routes.bp)
        
        # 2. Admin Routes
        from .admin import routes as admin_routes
        app.register_blueprint(admin_routes.bp, url_prefix='/admin')
        
        # 3. Legacy Flask-based CLI Commands
        # This section correctly imports the individual command modules from the `cli`
        # package. This is safe because `app/cli/__init__.py` is now a clean,
        # empty package marker, preventing any circular dependencies.
        from .cli import user_commands, system_commands, mindgate_commands
        app.register_blueprint(user_commands.users_cli)
        app.register_blueprint(system_commands.system_cli)
        app.register_blueprint(mindgate_commands.mindgate_cli)

    # We must import models at the end to make them known to SQLAlchemy.
    from . import models

    # --- [THE INTELLIGENCE NETWORK PROTOCOL] ---
    # Configure the application's logging system for production environments.
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
    
    # The final, fully assembled, and self-aware system is born.
    return app