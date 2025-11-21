# tests/smoke/test_database_service_smoke.py
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.factories import get_db_service as get_database_service
from app.services.database_service import DatabaseService


# Mock the DI functions to avoid actual dependencies
@pytest.fixture
def mock_di():
    with (
        patch("app.core.factories.get_db") as mock_get_db,
        patch("app.core.factories.get_logger") as mock_get_logger,
        patch("app.core.factories.get_settings") as mock_get_settings,
    ):
        mock_session = AsyncMock()
        mock_logger = MagicMock()
        mock_settings = MagicMock()

        mock_get_db.return_value = mock_session
        mock_get_logger.return_value = mock_logger
        mock_get_settings.return_value = mock_settings

        yield {
            "session": mock_session,
            "logger": mock_logger,
            "settings": mock_settings,
        }


def test_database_service_instantiation(mock_di):
    """
    Tests that the DatabaseService can be instantiated without errors.
    """
    service = get_database_service(
        session=mock_di["session"],
        logger=mock_di["logger"],
        settings=mock_di["settings"],
    )
    assert isinstance(service, DatabaseService)
    assert service.session == mock_di["session"]
    assert service.logger == mock_di["logger"]
    assert service.settings == mock_di["settings"]


@pytest.mark.asyncio
async def test_database_service_get_health(mock_di):
    """
    Tests that the get_database_health method can be called without errors.
    """
    # ARRANGE
    mock_session = AsyncMock()
    mock_session.execute.return_value = None
    mock_session.run_sync.return_value = [] # For inspect tables

    service = get_database_service(
        session=mock_session,
        logger=mock_di["logger"],
        settings=mock_di["settings"],
    )

    # Mock the inspect function to avoid real engine calls
    with patch("app.services.database_service.inspect") as mock_inspect:
        mock_inspector = MagicMock()
        mock_inspector.has_table.return_value = True
        mock_inspect.return_value = mock_inspector

        # ACT
        health = await service.get_database_health()

        # ASSERT
        assert health["status"] == "healthy"
        assert "connection" in health["checks"]


def test_backward_compatibility_wrapper(mock_di):
    """
    Tests that the deprecated wrapper function calls the new service method.
    """
    # This test requires running the async method in a loop, or mocking the helper
    # Since get_database_health wrapper uses _run_async, we mock the service method to return a coroutine

    from app.services.compat.database_compat import get_database_health

    async def mock_health():
        return {"status": "mocked"}

    with patch.object(DatabaseService, "get_database_health", side_effect=mock_health) as mock_method:
        # We also need to mock get_legacy_database_service to return a service with this mock
        with patch("app.services.compat.database_compat.get_legacy_database_service") as mock_get_legacy:
            mock_service = MagicMock()
            mock_service.get_database_health.side_effect = mock_health
            mock_get_legacy.return_value = mock_service

            result = get_database_health()

            assert result == {"status": "mocked"}
            mock_service.get_database_health.assert_called_once()
