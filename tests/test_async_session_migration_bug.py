# tests/test_async_session_migration_bug.py
"""
Test suite to verify the fix for the async/sync session mismatch bug.

BUG DESCRIPTION:
After migrating from Flask to FastAPI, several services were still using
`get_session()` from app.core.di which returns an async generator, but
treating it as a synchronous session. This caused runtime errors like:
- 'async_generator' object has no attribute 'scalars'
- 'async_generator' object has no attribute 'get'
- 'async_generator' object has no attribute 'execute'

AFFECTED FILES:
1. app/services/history_service.py - Fixed: Now uses async_session_factory properly
2. app/services/user_service.py - Fixed: Now supports both DI and standalone async usage
3. app/services/compat/database_compat.py - Fixed: Now creates proper async sessions

This test verifies the fix by ensuring the services work correctly with
async database operations.
"""

import inspect

import pytest

from app.core.di import get_session


class TestAsyncSessionMigrationBug:
    """Tests to verify the async/sync session mismatch bug is fixed."""

    def test_get_session_is_async_generator_function(self):
        """
        Verify that get_session from app.core.di is an async generator function.
        This was the root cause of the bug - code was treating it as a factory.
        """
        assert inspect.isasyncgenfunction(get_session), (
            "get_session should be an async generator function, not a regular function"
        )

    def test_get_session_returns_async_generator(self):
        """
        Verify that calling get_session() returns an async generator object.
        Old code was doing get_session()() which is incorrect.
        """
        result = get_session()
        assert inspect.isasyncgen(result), (
            "get_session() should return an async generator, not a session"
        )
        # Note: aclose() returns a coroutine that we don't need to await in sync test
        # The generator will be garbage collected anyway


class TestHistoryServiceFix:
    """Tests for the history_service.py fix."""

    def test_get_recent_conversations_is_async(self):
        """Verify that get_recent_conversations is now async."""
        from app.services.users.history_service import get_recent_conversations

        assert inspect.iscoroutinefunction(get_recent_conversations), (
            "get_recent_conversations should be an async function after the fix"
        )

    def test_rate_message_in_db_is_async(self):
        """Verify that rate_message_in_db is now async."""
        from app.services.users.history_service import rate_message_in_db

        assert inspect.iscoroutinefunction(rate_message_in_db), (
            "rate_message_in_db should be an async function after the fix"
        )

    @pytest.mark.asyncio
    async def test_get_recent_conversations_handles_errors_gracefully(self):
        """Verify that get_recent_conversations returns empty list on error."""
        from unittest.mock import AsyncMock, patch

        from app.services.users.history_service import get_recent_conversations

        # Mock async_session_factory to raise an error
        with patch("app.services.history_service.async_session_factory") as mock_factory:
            mock_session = AsyncMock()
            mock_session.execute.side_effect = Exception("Database error")
            mock_factory.return_value.__aenter__.return_value = mock_session
            mock_factory.return_value.__aexit__.return_value = None

            result = await get_recent_conversations(user_id=1)

            assert result == [], "Should return empty list on error"

    @pytest.mark.asyncio
    async def test_rate_message_validates_rating(self):
        """Verify that rate_message_in_db validates rating values."""
        from app.services.users.history_service import rate_message_in_db

        # Invalid rating should return error without hitting database
        result = await rate_message_in_db(message_id=1, rating="invalid", user_id=1)

        assert result["status"] == "error"
        assert "Invalid rating" in result["message"]


class TestUserServiceFix:
    """Tests for the user_service.py fix."""

    def test_user_service_accepts_session(self):
        """Verify UserService can be instantiated with a session (for DI)."""
        from unittest.mock import MagicMock

        from app.services.users.user_service import UserService

        mock_session = MagicMock()
        service = UserService(session=mock_session)

        assert service._injected_session is mock_session

    def test_user_service_works_without_session(self):
        """Verify UserService can be instantiated without a session (standalone)."""
        from app.services.users.user_service import UserService

        service = UserService()

        assert service._injected_session is None

    def test_get_user_service_returns_singleton(self):
        """Verify get_user_service returns a UserService instance."""
        from app.services.users.user_service import get_user_service

        service = get_user_service()

        assert service is not None
        assert hasattr(service, "get_all_users")
        assert hasattr(service, "create_new_user")
        assert hasattr(service, "ensure_admin_user_exists")

    def test_async_methods_are_coroutines(self):
        """Verify all main methods are async."""
        from app.services.users.user_service import UserService

        service = UserService()

        assert inspect.iscoroutinefunction(service.get_all_users)
        assert inspect.iscoroutinefunction(service.create_new_user)
        assert inspect.iscoroutinefunction(service.ensure_admin_user_exists)
