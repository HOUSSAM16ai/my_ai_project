# app/__init__.py - The Central Nervous System v6.0 (Fully Integrated & Aware)

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv

# --- PHASE 1: SYSTEM AWAKENING ---
# The system becomes self-aware by loading its environment. This is the first spark.
load_dotenv()

# --- PHASE 2: FORGING THE CORE ORGANS ---
# The core components are forged in a detached, universal state. They are pure
# potential, waiting to be connected to a central consciousness.
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
    This is the heart of creation. It doesn't just build an app; it forges a
    fully-aware, supercharged system by assembling all its independent parts.
    """
    app = Flask(__name__)
    
    # --- PHASE 3.1: CONSTITUTIONAL IMPRINTING ---
    # The system reads and imprints its core laws from the specified configuration.
    app.config.from_object(config_class_string)

    # --- PHASE 3.2: ORGAN-TO-BRAIN SYNAPTIC CONNECTION ---
    # The forged organs are now activated and neurally linked to the application.
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # --- PHASE 3.3: ACTIVATING THE PRIMARY NERVOUS SYSTEM (USER ROUTES) ---
    # The factory scans for the main user-facing blueprint and plugs it in.
    from app.routes import bp as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # --- PHASE 3.4: ACTIVATING THE SUPERCHARGED CMD MINISTRIES (THE GOD HAND) ---
    # This is the most powerful step. The system now scans the `cli` directory
    # and integrates all command ministries, giving the Architect direct control.
    
    # Ministry of User Affairs
    from app.cli.user_commands import users_cli
    app.register_blueprint(users_cli)
    
    # Ministry of the Mind Gate (AI Interaction)
    from app.cli.mindgate_commands import mindgate_cli
    app.register_blueprint(mindgate_cli)

    # In the future, you will simply add new ministries here. The structure is eternal.
    # from app.cli.project_commands import projects_cli
    # app.register_blueprint(projects_cli)

    # The final, fully assembled, supercharged system is born.
    return app