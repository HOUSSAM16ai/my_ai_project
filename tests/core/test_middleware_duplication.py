from unittest.mock import MagicMock, patch

import pytest

from app.main import create_app
from app.middleware.remove_blocking_headers import RemoveBlockingHeadersMiddleware
from app.middleware.security.rate_limit_middleware import RateLimitMiddleware


@pytest.mark.asyncio
async def test_middleware_chaos_interference():
    """
    Diagnoses the 'Chaotic Constructive Interference' (Duplicate Middleware).
    Verifies that critical defense systems are not piling up on each other.
    """
    # 1. Reset Global State (The "Singularity")
    import app.main

    app.main._kernel_instance = None

    # 2. Mock Settings to simulate PRODUCTION environment
    # We must ensure the Kernel sees "production" so it adds RateLimitMiddleware.
    with patch("app.kernel.RealityKernel.__init__", return_value=None):
        # Actually, mocking init is hard because we need the object to work.
        pass

    # Better strategy: Patch the settings dict passed to Kernel
    # The Kernel is initialized in get_kernel using get_settings().model_dump()

    # We will patch get_settings to return a config with ENVIRONMENT="production"
    with patch("app.main.get_settings") as mock_get_settings:
        mock_settings = MagicMock()
        # Mocking model_dump to return our desired config
        mock_settings.model_dump.return_value = {
            "ENVIRONMENT": "production",
            "PROJECT_NAME": "CogniForge",
            "ALLOWED_HOSTS": ["*"],
            "BACKEND_CORS_ORIGINS": ["*"],
            "FRONTEND_URL": "http://localhost:3000",
        }
        # Also mock dictionary access for direct usage if any
        mock_settings.get.side_effect = lambda k, d=None: mock_settings.model_dump.return_value.get(
            k, d
        )

        mock_get_settings.return_value = mock_settings

        # 3. Create the app
        fastapi_app = create_app()

        # 4. Inspect the "Reality Fabric" (Middleware Stack)
        middleware_stack = fastapi_app.user_middleware

        rate_limit_count = 0
        remove_headers_count = 0

        for middleware in middleware_stack:
            if middleware.cls == RateLimitMiddleware:
                rate_limit_count += 1
            if middleware.cls == RemoveBlockingHeadersMiddleware:
                remove_headers_count += 1

        # 5. Diagnosis & Verification
        print(f"\n[DIAGNOSIS] RateLimitMiddleware Count: {rate_limit_count}")
        print(f"[DIAGNOSIS] RemoveBlockingHeadersMiddleware Count: {remove_headers_count}")

        # In Production, we expect RateLimitMiddleware exactly ONCE.
        # Previously (the bug), it would have been 2 (or 1 if testing masked it).
        assert rate_limit_count == 1, (
            f"Constructive Interference Detected! RateLimitMiddleware count is {rate_limit_count}"
        )

        # We also expect RemoveBlockingHeadersMiddleware exactly ONCE.
        assert remove_headers_count == 1, (
            f"Defense System Breach! RemoveBlockingHeadersMiddleware count is {remove_headers_count}"
        )
