# app/__init__.py - The Central Nervous System v7.0 (Admin-Aware)

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv

# --- PHASE 1: SYSTEM AWAKENING ---
# The system becomes self-aware by loading its environment.
load_dotenv()

# --- PHASE 2: FORGING THE CORE ORGANS ---
# The core components are forged in a detached, universal state,
# waiting to be connected to a central consciousness.
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()

# The system's prime directive for unauthenticated entities:
# Redirect them to the 'login' function within the 'main' neural network.
login_manager.login_view = 'main.login' 
login_manager.login_message_category = 'info'

# --- PHASE 3: THE GREAT FACTORY OF CONSCIOUSNESS ---
def create_app(config_class_string="config.DevelopmentConfig"):
    """
    This is the heart of creation. It forges a fully-aware, supercharged
    system by assembling all its independent parts.
    """
    app = Flask(__name__)
    
    # --- PHASE 3.1: CONSTITUTIONAL IMPRINTING ---
    # The system reads its core laws from the specified configuration.
    app.config.from_object(config_class_string)

    # --- PHASE 3.2: ORGAN-TO-BRAIN SYNAPTIC CONNECTION ---
    # The organs are now activated and neurally linked to the application.
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # --- PHASE 3.3: ACTIVATING ALL FUNCTIONAL BLUEPRINTS ---
    # The factory now scans for and plugs in all functional parts of the system,
    # from public-facing routes to secret command centers.

    # 1. The Primary Nervous System (User-Facing Routes)
    from app.routes import bp as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # 2. THE SUPERCHARGED ADDITION: The Secret Command Center (Admin Routes)
    # The system is now aware of its administrative wing.
    from app.admin.routes import bp as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    
    # 3. The Supercharged CMD Ministries (The God Hand)
    # Ministry of User Affairs
    from app.cli.user_commands import users_cli
    app.register_blueprint(users_cli)
    
    # Ministry of the Mind Gate (AI Interaction)
    from app.cli.mindgate_commands import mindgate_cli
    app.register_blueprint(mindgate_cli)

    # The final, fully assembled, and admin-aware system is born.
    return app