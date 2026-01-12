import os
from unittest.mock import patch

import pytest

from app.core.database import create_db_engine
from app.core.settings.base import BaseServiceSettings

# -----------------------------------------------------------------------------
# GUARDRAIL: DATABASE CONNECTION SECURITY & STABILITY
# -----------------------------------------------------------------------------
# This test suite is a NON-NEGOTIABLE LAW against the "Supabase Transaction Pooler"
# disaster. It enforces strict handling of:
# 1. URL-encoded passwords (e.g. '%40' for '@').
# 2. 'sslmode' stripping for 'asyncpg' compatibility.
# 3. Correct SSLContext injection for secure connections.
#
# DO NOT MODIFY OR DELETE WITHOUT ARCHITECT APPROVAL.
# -----------------------------------------------------------------------------


class MockSettings(BaseServiceSettings):
    DATABASE_URL: str = "postgresql://user:pass%40word@host:5432/db?sslmode=require"
    SERVICE_NAME: str = "guardrail_test_service"
    ENVIRONMENT: str = "testing"


@pytest.mark.asyncio
@patch("app.core.database.create_async_engine")
async def test_guardrail_db_url_password_encoding(mock_create_engine):
    """
    CRITICAL: Verifies that special characters in passwords (URL encoded) are NOT
    lost or double-decoded during the `make_url` -> `render_as_string` roundtrip.

    Failure scenario: 'pass%40word' becomes 'pass@word' in the string, causing
    parsing ambiguity if the user uses '@' in their password.
    """
    # Clear env to enforce MockSettings
    with patch.dict(os.environ, {}, clear=True):
        settings = MockSettings()
        create_db_engine(settings)

        args, _ = mock_create_engine.call_args
        db_url = args[0]

        # STRICT CHECK 1: Password must retain encoding if it was encoded in the input
        # The exact string format might vary by driver (postgresql+asyncpg://), but the
        # password segment 'pass%40word' MUST be present.
        assert "pass%40word" in db_url, (
            f"❌ CATASTROPHIC FAILURE: Password encoding lost. Expected 'pass%40word' in '{db_url}'"
        )

        # STRICT CHECK 2: No '***' masking
        assert "***" not in db_url, (
            "❌ CATASTROPHIC FAILURE: Password masked in connection string. "
            "Database will fail to authenticate."
        )


@pytest.mark.asyncio
@patch("app.core.database.create_async_engine")
async def test_guardrail_ssl_mode_handling(mock_create_engine):
    """
    CRITICAL: Verifies that 'sslmode' is stripped from the URL (causing asyncpg crashes)
    and correctly converted to a Python SSLContext.
    """
    with patch.dict(os.environ, {}, clear=True):
        settings = MockSettings()
        create_db_engine(settings)

        args, kwargs = mock_create_engine.call_args
        db_url = args[0]
        connect_args = kwargs.get("connect_args", {})

        # STRICT CHECK 3: sslmode param removal
        assert "sslmode" not in db_url, (
            "❌ FAILURE: 'sslmode' parameter persists in URL. "
            "Asyncpg will crash with 'unexpected keyword argument'."
        )

        # STRICT CHECK 4: SSLContext Injection
        assert "ssl" in connect_args, "❌ FAILURE: SSL Context not injected into connect_args."

        ssl_ctx = connect_args["ssl"]
        # STRICT CHECK 5: Hostname check disabled for Pooler compatibility
        # (Supabase poolers often present certs that don't match the alias strictly)
        assert ssl_ctx.check_hostname is False, (
            "❌ FAILURE: SSL check_hostname must be False for Transaction Pooler compatibility."
        )
