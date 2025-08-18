# app/__init__.py - The Unified & Environment-Aware Factory (v8.0)

from flask import Flask
from config import config_by_name # <-- نستورد "الدساتير" المتعددة
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- [PHASE 1: FORGING THE CORE ORGANS] ---
# Core components are created in a universal state.
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'main.login' 
login_manager.login_message_category = 'info'

# --- [PHASE 2: THE GREAT FACTORY OF CONSCIOUSNESS] ---
def create_app(config_name: str = "development"):
    """
    The heart of creation. It assembles all parts of the system
    based on the specified environment (development, production, etc.).
    """
    app = Flask(__name__)
    
    # --- [STEP 2.1: CONSTITUTIONAL IMPRINTING] ---
    # The system reads its laws from the correct configuration class.
    config_object = config_by_name.get(config_name)
    app.config.from_object(config_object)

    # --- [STEP 2.2: ORGAN-TO-BRAIN SYNAPTIC CONNECTION] ---
    # Core organs are now activated and linked to the application.
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # --- [STEP 2.3: ACTIVATING ALL FUNCTIONAL BLUEPRINTS] ---
    # All functional parts of the system are now plugged in.
    # This must be done within an app context to avoid circular imports.
    with app.app_context():
        # 1. The Primary Nervous System (User-Facing Routes)
        from . import routes
        app.register_blueprint(routes.bp)
        
        # 2. The Secret Command Center (Admin Routes)
        from .admin import routes as admin_routes
        app.register_blueprint(admin_routes.bp, url_prefix='/admin')
        
        # 3. The Supercharged CMD Ministries (The God Hand)
        from .cli import user_commands, system_commands, mindgate_commands
        app.register_blueprint(user_commands.users_cli)
        app.register_blueprint(system_commands.system_cli)
        app.register_blueprint(mindgate_commands.mindgate_cli)

    # We must import models at the end, after db is defined, to make them known to SQLAlchemy.
    from . import models

    # The final, fully assembled, and environment-aware system is born.
    return app