from unittest.mock import MagicMock

import pytest

from app.services.database_service import DatabaseService

# tests/smoke/test_database_service_smoke.py

@pytest.mark.skip(reason="Legacy test for an old architecture. Needs complete rewrite.")
@pytest.mark.asyncio
async def test_database_health_check():
    # Mock session
    mock_session = MagicMock()
    service = DatabaseService(session=mock_session)

    # Mock execute
    mock_session.execute = MagicMock()

    health = await service.check_health()
    assert health["status"] == "healthy"
