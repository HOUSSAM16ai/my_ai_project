# app/middleware/adapters/flask_adapter.py
# ======================================================================================
# ==                    FLASK ADAPTER (v∞)                                          ==
# ======================================================================================
"""
مُحوّل Flask - Flask Adapter

Adapts the middleware system to Flask applications.
"""

from flask import Flask

from app.middleware.core.pipeline import SmartPipeline


class FlaskAdapter:
    """
    Flask Adapter

    Integrates the middleware pipeline with Flask applications.
    """

    def __init__(self, app: Flask | None = None, pipeline: SmartPipeline | None = None):
        """
        Initialize Flask adapter

        Args:
            app: Flask application
            pipeline: Middleware pipeline
        """
        self.pipeline = pipeline or SmartPipeline()

        if app:
            self.init_app(app)

    def init_app(self, app: Flask):
        """
        Initialize adapter with Flask app

        Args:
            app: Flask application
        """
        from flask import g, request

        from app.middleware.core.context import RequestContext
        from app.middleware.core.response_factory import ResponseFactory

        @app.before_request
        def before_request():
            """Process request through pipeline"""
            ctx = RequestContext.from_flask_request(request)
            result = self.pipeline.run(ctx)

            g.middleware_ctx = ctx
            g.middleware_result = result

            if not result.is_success:
                return ResponseFactory.from_middleware_result(result, framework="flask")

        @app.after_request
        def after_request(response):
            """Add headers from context"""
            if hasattr(g, "middleware_ctx"):
                # Add any metadata headers
                cors_headers = g.middleware_ctx.get_metadata("cors_headers", {})
                for key, value in cors_headers.items():
                    response.headers[key] = value

            return response
