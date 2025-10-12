# app/__init__.py
# ======================================================================================
# ==                 THE GENESIS FACTORY (v11.0 • Overmind Resurgence)                ==
# ======================================================================================
# PRIME DIRECTIVE:
#   نقطة الخلق الوحيدة للتطبيق. تبني الكيان (Flask App) وتربط الأعضاء الحيوية:
#   قاعدة البيانات، تسجيل الدخول، الأوامر (CLI)، مخططي Overmind (Planners)،
#   وخدمات التوليد (Maestro / LLM).
#
# WHAT'S NEW (v11.0 vs v10.0):
#   1. حل جذري لمشكلة "Working outside of application context" في أوامر mindgate:
#       - توفير كائن app عالمي (app = create_app()) لدعم نمط FLASK_APP=app.
#       - الحفاظ على دعم نمط المصنع (factory) FLASK_APP='app:create_app'.
#       - توثيق واضح لكيفية التفعيل.
#   2. تقسيم واضح لدوال التسجيل (extensions / blueprints / logging / planner warmup).
#   3. دعم متغيرات بيئة للتحكم:
#        FLASK_CONFIG=production|development|testing|default
#        OVERMIND_EAGER_DISCOVER=1   → اكتشاف البلانرز مبكراً (اختياري).
#        OVERMIND_WARM_PLANNERS=1    → تهيئة (instantiate) البلانرز عند الإقلاع.
#   4. حماية آمنة من فشل اكتشاف المخططين (لا يمنع التطبيق من الإقلاع).
#   5. تفعيل سجل (Logger) متماسك مع fallback في البيئات غير الإنتاجية.
#   6. توفير دالة ensure_app_context() للاستخدام في سكربتات خارجية.
#
# QUICK START:
#   (أ) التعيين التقليدي:
#       export FLASK_APP=app
#       flask mindgate plan "Write README"
#   (ب) نمط المصنع:
#       export FLASK_APP='app:create_app'
#       flask mindgate plan "Write README"
#
#   إذا ظهر مجدداً الخطأ Working outside of application context:
#       - تأكد من أن FLASK_APP مضبوط كما أعلاه.
#       - أو استعمل ensure_app_context() في سكربت خارجي قبل استدعاء الخدمات.
#
# ======================================================================================

from __future__ import annotations

import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Optional, Callable

from flask import Flask, current_app
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from dotenv import load_dotenv

# --------------------------------------------------------------------------------------
# Load .env FIRST (env overrides must exist before config object import)
# --------------------------------------------------------------------------------------
load_dotenv()

# --------------------------------------------------------------------------------------
# Extensions (instantiated once; bound inside create_app)
# --------------------------------------------------------------------------------------
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "main.login"
login_manager.login_message_category = "info"

# --------------------------------------------------------------------------------------
# Configuration mapping (import late enough to allow env to load)
# --------------------------------------------------------------------------------------
from config import config_by_name  # noqa: E402

# --------------------------------------------------------------------------------------
# Internal Helpers
# --------------------------------------------------------------------------------------
def _choose_config_name(explicit: Optional[str]) -> str:
    """
    Decide which configuration profile to load.
    Order of precedence:
      1. Function argument
      2. Environment FLASK_CONFIG
      3. Fallback 'default'
    """
    return explicit or os.getenv("FLASK_CONFIG", "default")


def _register_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    
    # Setup enterprise-grade middleware
    try:
        from app.middleware import setup_error_handlers, setup_cors, setup_request_logging
        setup_error_handlers(app)
        setup_cors(app)
        setup_request_logging(app)
        app.logger.info("Enterprise middleware initialized successfully")
    except Exception as exc:
        app.logger.warning("Failed to initialize middleware: %s", exc, exc_info=True)
    
    # Setup Swagger/OpenAPI documentation (optional)
    try:
        from app.swagger_integration import init_swagger
        init_swagger(app)
        app.logger.info("Swagger documentation enabled at /api/docs/")
    except Exception as exc:
        app.logger.warning("Failed to initialize Swagger: %s (continuing without it)", exc)


def _register_blueprints(app: Flask) -> None:
    # تأكد أن الاستيراد يتم داخل السياق لتفادي دوائر الاستيراد
    from . import routes
    app.register_blueprint(routes.bp)

    from .admin import routes as admin_routes
    app.register_blueprint(admin_routes.bp, url_prefix="/admin")
    
    # Register World-Class API Gateway blueprints
    from .api import init_api
    init_api(app)

    from .cli import user_commands, mindgate_commands, database_commands
    app.register_blueprint(user_commands.users_cli)
    app.register_blueprint(mindgate_commands.mindgate_cli)
    app.register_blueprint(database_commands.database_cli)


def _configure_logging(app: Flask) -> None:
    """
    Production-grade logging with safe repeat-initialization guard.
    """
    if app.logger.handlers and not app.debug and not app.testing:
        # Already configured externally (e.g., gunicorn)
        return

    log_level_name = app.config.get("APP_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, log_level_name, logging.INFO)
    app.logger.setLevel(level)

    if app.debug or app.testing:
        # Rely on default Flask console logger
        app.logger.debug("Debug/Test logging active.")
        return

    # Production / non-debug
    if not os.path.exists("logs"):
        os.mkdir("logs")

    file_handler = RotatingFileHandler(
        "logs/cogniforge.log", maxBytes=1024 * 1024 * 5, backupCount=5
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s "
            "[in %(pathname)s:%(lineno)d]"
        )
    )
    file_handler.setLevel(level)
    # Avoid duplicate handlers
    if not any(isinstance(h, RotatingFileHandler) for h in app.logger.handlers):
        app.logger.addHandler(file_handler)

    app.logger.info("Logging subsystem initialized (level=%s)", log_level_name)


def _import_models(app: Flask) -> None:
    """
    Import models so Alembic / SQLAlchemy can see metadata.
    """
    try:
        from . import models  # noqa: F401
        app.logger.debug("Models imported successfully.")
    except Exception as exc:
        app.logger.error("Failed to import models: %s", exc, exc_info=True)


def _planner_discovery(app: Flask) -> None:
    """
    Optionally discover & warm planners early, controlled by env flags.
      OVERMIND_EAGER_DISCOVER=1
      OVERMIND_WARM_PLANNERS=1
    """
    eager = os.getenv("OVERMIND_EAGER_DISCOVER", "0") == "1"
    warm = os.getenv("OVERMIND_WARM_PLANNERS", "0") == "1"
    if not eager and not warm:
        return

    try:
        from app.overmind.planning import factory as planning_factory
    except Exception as exc:
        app.logger.warning("Planner factory import failed (skip discovery): %s", exc)
        return

    try:
        planning_factory.discover(force=True)
        stats = planning_factory.planner_stats()
        app.logger.info(
            "Planner discovery complete (count=%s, duration=%.4f)",
            stats.get("planner_count"),
            stats.get("last_discovery_duration"),
        )
        if warm:
            report = planning_factory.warm_up()
            app.logger.info("Planner warm-up report: %s", report)
    except Exception as exc:
        app.logger.warning("Planner discovery/warm failed: %s", exc, exc_info=True)


def _register_shutdown_signals(app: Flask) -> None:
    """
    Placeholder for hooking signals/teardown logic (thread pools, caches, etc.).
    """
    @app.teardown_appcontext
    def _teardown(exc):
        # Add resource cleanup if needed
        if exc:
            app.logger.debug("App context teardown with exception: %s", exc)


# --------------------------------------------------------------------------------------
# Public Factory
# --------------------------------------------------------------------------------------
def create_app(config_name: Optional[str] = None) -> Flask:
    """
    Create and configure a Flask application instance.

    Args:
        config_name: Optional configuration profile name; overrides FLASK_CONFIG env.

    Returns:
        A fully initialized Flask application.
    """
    chosen = _choose_config_name(config_name)
    app = Flask(__name__)

    config_obj = config_by_name.get(chosen)
    if config_obj is None:
        raise RuntimeError(f"Unknown config profile '{chosen}'")
    app.config.from_object(config_obj)

    # Register core pieces
    _register_extensions(app)
    _configure_logging(app)

    # Use app context for blueprint registration & dependent imports
    with app.app_context():
        _register_blueprints(app)
        _import_models(app)
        _planner_discovery(app)
        _register_shutdown_signals(app)

    app.logger.info("Application created with profile '%s'", chosen)
    return app


# --------------------------------------------------------------------------------------
# Global App (Supports FLASK_APP=app)
# --------------------------------------------------------------------------------------
# Providing a global instance helps CLI usage when user sets FLASK_APP=app.
# If you prefer pure factory mode, you can ignore this and set FLASK_APP='app:create_app'
#
# Smart initialization: Skip global app creation in test environments to avoid
# premature database connection attempts before test fixtures are ready.
app = None  # type: ignore

def _should_create_global_app() -> bool:
    """Determine if we should create a global app instance at module import time."""
    # Skip if we're in a test environment
    if os.getenv("TESTING") == "1" or os.getenv("FLASK_ENV") == "testing":
        return False
    # Skip if pytest is running (detected by PYTEST_CURRENT_TEST env var)
    if "PYTEST_CURRENT_TEST" in os.environ:
        return False
    return True

if _should_create_global_app():
    try:
        app = create_app()
    except Exception as _global_exc:  # Fail softly so unit tests can still import modules.
        # We do a minimal fallback logger
        _fallback_logger = logging.getLogger("genesis.factory")
        _fallback_logger.error("Global app instantiation failed: %s", _global_exc, exc_info=True)
        app = None  # type: ignore


# --------------------------------------------------------------------------------------
# Utility: Ensure Context (for scripts / notebook usage)
# --------------------------------------------------------------------------------------
def ensure_app_context() -> Flask:
    """
    Ensure there is an active application context.
    Returns the app instance in context.
    """
    if current_app:
        return current_app._get_current_object()  # already inside context

    global app
    if app is None:
        app = create_app()
    ctx = app.app_context()
    ctx.push()
    return app


# --------------------------------------------------------------------------------------
# Optional: Simple health check (import-level)
# --------------------------------------------------------------------------------------
def health_probe() -> dict:
    """
    Lightweight introspection for external tooling.
    """
    return {
        "app_created": app is not None,
        "config": getattr(app, "config", {}).get("ENV") if app else None,
        "has_db": db is not None,
        "login_manager": login_manager is not None,
        "version": "v11.0",
    }


__all__ = [
    "create_app",
    "ensure_app_context",
    "db",
    "login_manager",
    "migrate",
    "health_probe",
    "app",
]