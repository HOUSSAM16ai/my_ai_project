import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.system_service import system_service
from sqlalchemy.exc import OperationalError

@pytest.mark.asyncio
async def test_check_database_status_healthy():
    """Test that check_database_status returns 'healthy' when the database is accessible."""
    mock_db = AsyncMock()
    mock_db.execute.return_value = None  # Simulate successful execution

    status = await system_service.check_database_status(mock_db)

    assert status == "healthy"
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_check_database_status_unhealthy():
    """Test that check_database_status returns 'unhealthy' when the database raises an exception."""
    mock_db = AsyncMock()
    mock_db.execute.side_effect = OperationalError("Connection failed", {}, None)

    status = await system_service.check_database_status(mock_db)

    assert status == "unhealthy"
    mock_db.execute.assert_called_once()

@pytest.mark.asyncio
async def test_is_database_connected_true():
    """Test that is_database_connected returns True when status is healthy."""
    # We can mock check_database_status, but since it's an instance method,
    # and we want to test the class integration, mocking the DB is better.
    mock_db = AsyncMock()
    mock_db.execute.return_value = None

    connected = await system_service.is_database_connected(mock_db)

    assert connected is True

@pytest.mark.asyncio
async def test_is_database_connected_false():
    """Test that is_database_connected returns False when status is unhealthy."""
    mock_db = AsyncMock()
    mock_db.execute.side_effect = Exception("DB Down")

    connected = await system_service.is_database_connected(mock_db)

    assert connected is False
