from unittest.mock import AsyncMock

import pytest

from app.services.system.database_service import DatabaseService

# tests/smoke/test_database_service_smoke.py


@pytest.mark.asyncio
async def test_database_health_check():
    # Mock session
    mock_session = AsyncMock()
    service = DatabaseService(session=mock_session)

    health = await service.check_health()
    assert health["status"] == "healthy"
