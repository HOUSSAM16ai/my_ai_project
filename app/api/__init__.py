# app/api/__init__.py
# ======================================================================================
# ==             WORLD-CLASS API GATEWAY - UNIFIED ENTRY POINT                      ==
# ======================================================================================
# PRIME DIRECTIVE:
#   نقطة دخول موحدة لجميع عمليات API الخارقة
#   Unified entry point for all superhuman API operations
#
# Features:
#   - RESTful CRUD operations for all resources
#   - API versioning (v1, v2, v3)
#   - Integrated security, observability, and contract validation
#   - Enterprise-grade error handling
#   - OpenAPI/Swagger documentation
#   - Rate limiting and caching
#   - Zero-Trust security model

from flask import Blueprint

# Create API blueprint with versioning support
api_bp = Blueprint("api", __name__, url_prefix="/api")
api_v1_bp = Blueprint("api_v1", __name__, url_prefix="/api/v1")
api_v2_bp = Blueprint("api_v2", __name__, url_prefix="/api/v2")


def init_api(app):
    """Initialize API blueprints with all services"""
    from app.api import (
        analytics_routes,
        crud_routes,
        developer_portal_routes,
        docs_routes,
        gateway_routes,
        observability_routes,
        security_routes,
        stream_routes,
        subscription_routes,
    )

    # Register blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(api_v1_bp)
    app.register_blueprint(api_v2_bp)

    # Register superhuman enhancement routes
    app.register_blueprint(subscription_routes.api_bp)
    app.register_blueprint(developer_portal_routes.api_bp)
    app.register_blueprint(analytics_routes.api_bp)

    # Register SSE streaming routes
    app.register_blueprint(stream_routes.bp)
    app.logger.info("🌊 SSE Streaming routes registered at /api/v1/stream")

    # Register intelligent platform routes
    try:
        from app.api import intelligent_platform_routes

        app.register_blueprint(intelligent_platform_routes.intelligent_platform_bp)
        app.logger.info("🔥 Intelligent Service Platform routes registered")
    except Exception as exc:
        app.logger.warning("Failed to register Intelligent Platform routes: %s", exc)

    app.logger.info("🚀 World-Class API Gateway initialized successfully")
    app.logger.info("📡 API endpoints available at /api, /api/v1, /api/v2")
    app.logger.info("📚 API Documentation available at /api/docs")
    app.logger.info(
        "🔥 SUPERHUMAN enhancements: Subscriptions, Developer Portal, Analytics, Intelligent Platform, SSE Streaming"
    )
