# tests/test_middleware_decorators.py
# ======================================================================================
# ==                    MIDDLEWARE DECORATORS IMPORT TEST                           ==
# ======================================================================================
"""
Test suite to verify middleware decorators can be imported correctly.
This test prevents regression of the ImportError that was previously occurring.
"""


class TestMiddlewareDecorators:
    """Test middleware decorator imports and basic functionality."""

    def test_can_import_decorators_from_middleware_package(self):
        """
        Test that decorators can be imported from app.middleware.decorators package.

        This test ensures that the decorators package __init__.py correctly
        exports the required decorators, preventing the ImportError:
        "cannot import name 'monitor_performance' from 'app.middleware.decorators'"
        """
        from app.middleware.decorators import (
            monitor_performance,
            rate_limit,
            require_jwt_auth,
        )

        # Verify all decorators are callable
        assert callable(monitor_performance), "monitor_performance should be callable"
        assert callable(rate_limit), "rate_limit should be callable"
        assert callable(require_jwt_auth), "require_jwt_auth should be callable"

    def test_decorators_are_functions(self):
        """Test that imported decorators are function objects."""
        from app.middleware.decorators import (
            monitor_performance,
            rate_limit,
            require_jwt_auth,
        )

        # Check they're functions (decorators)
        assert hasattr(monitor_performance, "__call__")
        assert hasattr(rate_limit, "__call__")
        assert hasattr(require_jwt_auth, "__call__")

    def test_decorators_module_has_correct_exports(self):
        """Test that __all__ contains expected decorator names."""
        from app.middleware import decorators

        # Verify __all__ is defined and contains our decorators
        assert hasattr(decorators, "__all__"), "decorators module should define __all__"
        assert "monitor_performance" in decorators.__all__
        assert "rate_limit" in decorators.__all__
        assert "require_jwt_auth" in decorators.__all__

    def test_can_import_in_api_routes_pattern(self):
        """
        Test the actual import pattern used in API routes.

        This mirrors the import used in:
        - app/api/analytics_routes.py
        - app/api/developer_portal_routes.py
        - app/api/subscription_routes.py
        """
        # This should not raise ImportError
        from app.middleware.decorators import (
            monitor_performance,
            rate_limit,
            require_jwt_auth,
        )

        # Verify we got actual decorator functions
        assert monitor_performance is not None
        assert rate_limit is not None
        assert require_jwt_auth is not None


class TestDecoratorSources:
    """Test that decorators are properly exported from their source services."""

    def test_monitor_performance_from_observability_service(self):
        """Verify monitor_performance is available from its source service."""
        from app.services.api_observability_service import monitor_performance

        assert callable(monitor_performance)

    def test_security_decorators_from_security_service(self):
        """Verify security decorators are available from their source service."""
        from app.services.api_security_service import rate_limit, require_jwt_auth

        assert callable(rate_limit)
        assert callable(require_jwt_auth)

    def test_decorator_identity_consistency(self):
        """
        Verify that importing from decorators package gives same objects
        as importing from source services.
        """
        from app.middleware.decorators import (
            monitor_performance as mp_from_decorators,
        )
        from app.middleware.decorators import rate_limit as rl_from_decorators
        from app.services.api_observability_service import (
            monitor_performance as mp_from_service,
        )
        from app.services.api_security_service import rate_limit as rl_from_service

        # They should be the exact same objects (not copies)
        assert mp_from_decorators is mp_from_service
        assert rl_from_decorators is rl_from_service
