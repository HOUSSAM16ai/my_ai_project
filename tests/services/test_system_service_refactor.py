# tests/services/test_system_service_refactor.py
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from app.services.system_service import SystemService

@pytest.mark.asyncio
async def test_verify_system_integrity_healthy():
    service = SystemService()

    mock_session = AsyncMock()
    # First call is SELECT 1, second is SELECT User
    # we need to setup execution results

    # Mock result for SELECT 1
    mock_result_1 = MagicMock()

    # Mock result for SELECT User
    mock_result_2 = MagicMock()
    mock_result_2.scalars.return_value.first.return_value = True # Admin present

    mock_session.execute.side_effect = [mock_result_1, mock_result_2]

    # Mock the context manager factory
    mock_factory = MagicMock()
    mock_factory.__aenter__.return_value = mock_session
    mock_factory.__aexit__.return_value = None

    with patch("app.services.system_service.async_session_factory", return_value=mock_factory):
        result = await service.verify_system_integrity()

    assert result["status"] == "ok"
    assert result["admin_present"] is True
    assert result["db"] == "connected"

@pytest.mark.asyncio
async def test_verify_system_integrity_db_down():
    service = SystemService()

    # Mock failure
    mock_factory = MagicMock()
    mock_factory.__aenter__.side_effect = Exception("DB Down")

    with patch("app.services.system_service.async_session_factory", return_value=mock_factory):
        result = await service.verify_system_integrity()

    assert result["db"] == "unreachable"
    assert result["admin_present"] is False
