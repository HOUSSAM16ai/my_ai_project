
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.services.platform_boundary_service import PlatformBoundaryService, get_platform_boundary_service
from app.api.routers import observability

@pytest.fixture
def mock_platform_boundary():
    """Mocks the PlatformBoundaryService."""
    mock_service = MagicMock(spec=PlatformBoundaryService)

    # Mock data mesh
    mock_service.data_mesh = MagicMock()
    mock_service.data_mesh.get_mesh_metrics.return_value = {"active_contracts": 5}

    # Mock AIOps
    mock_service.aiops = MagicMock()
    mock_service.aiops.get_aiops_metrics.return_value = {"anomalies_detected": 0}

    # Mock GitOps
    mock_service.gitops = MagicMock()
    mock_service.gitops.get_gitops_metrics.return_value = {"sync_status": "synced"}

    # Mock Observability
    mock_snapshot = MagicMock()
    mock_snapshot.timestamp = "2025-01-01T00:00:00Z"
    mock_service.observability = MagicMock()
    mock_service.observability.get_performance_snapshot.return_value = mock_snapshot
    mock_service.get_performance_snapshot = AsyncMock(return_value=mock_snapshot)

    # Mock get_platform_overview
    mock_service.get_platform_overview = AsyncMock(return_value={
        "data_mesh": {"active_contracts": 5},
        "aiops": {"anomalies_detected": 0},
        "gitops": {"sync_status": "synced"},
        "workflows": {},
        "edge_multicloud": {},
        "sre": {},
        "observability": {
            "snapshot": mock_snapshot,
            "compliance": {"status": "compliant"}
        }
    })

    return mock_service

@pytest.mark.asyncio
async def test_observability_router_get_metrics(mock_platform_boundary):
    """Test the /metrics endpoint using the Platform Boundary."""
    response = await observability.get_metrics(platform_service=mock_platform_boundary)

    assert response["status"] == "success"
    assert "metrics" in response
    assert "api_performance" in response["metrics"]
    assert "aiops_health" in response["metrics"]

    # OPTIMIZATION check: Ensure we call specific methods, NOT the heavy overview
    mock_platform_boundary.get_performance_snapshot.assert_called_once()
    mock_platform_boundary.aiops.get_aiops_metrics.assert_called_once()
    # Ensure heavy method is NOT called
    mock_platform_boundary.get_platform_overview.assert_not_called()

@pytest.mark.asyncio
async def test_observability_router_get_aiops_metrics(mock_platform_boundary):
    """Test the /metrics/aiops endpoint delegating to Platform Boundary."""
    response = await observability.get_aiops_metrics(platform_service=mock_platform_boundary)

    assert response["ok"] is True
    assert response["data"] == {"anomalies_detected": 0}
    mock_platform_boundary.aiops.get_aiops_metrics.assert_called()

@pytest.mark.asyncio
async def test_observability_router_get_performance_snapshot(mock_platform_boundary):
    """Test the /performance/snapshot endpoint."""
    response = await observability.get_performance_snapshot(platform_service=mock_platform_boundary)

    assert response["status"] == "success"
    mock_platform_boundary.get_performance_snapshot.assert_called()
