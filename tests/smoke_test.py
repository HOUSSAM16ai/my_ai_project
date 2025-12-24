"""
Smoke Test for Reality Kernel and Overmind Assembly.
This test verifies that the core components can be instantiated without runtime errors.
"""
import pytest
from app.kernel import RealityKernel
from app.services.overmind.factory import create_overmind
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_kernel_initialization():
    """Verify RealityKernel initializes with valid settings."""
    settings = {"DATABASE_URL": "sqlite+aiosqlite:///:memory:", "SECRET_KEY": "x" * 32, "ENVIRONMENT": "testing"}
    kernel = RealityKernel(settings)
    app = kernel.get_app()
    # Adjust expectation based on testing environment override
    assert "CogniForge" in app.title

@pytest.mark.asyncio
async def test_overmind_assembly():
    """Verify Overmind factory assembles components correctly."""
    # Mock DB Session
    mock_db = AsyncMock()

    # We might need to mock get_registry or other internal deps if they do IO
    # For now, let's see if it works with just the DB mock
    try:
        orchestrator = await create_overmind(mock_db)
        assert orchestrator is not None
        assert orchestrator.brain is not None
        assert orchestrator.executor is not None
    except Exception as e:
        pytest.fail(f"Overmind assembly failed: {e}")
