# tests/services/test_api_governance_service.py
import pytest

from app.services.api_governance_service import (
    CosmicGovernanceService,
    get_governance_service,
    governance_service,
)


def test_api_governance_service_instantiation():
    """Test that the governance service is instantiated correctly."""
    assert governance_service is not None
    assert isinstance(governance_service, CosmicGovernanceService)
    assert get_governance_service() is governance_service

def test_governance_service_methods():
    """Test basic method availability (static methods)."""
    assert hasattr(CosmicGovernanceService, "create_existential_protocol")
    assert hasattr(CosmicGovernanceService, "create_cosmic_council")

@pytest.mark.asyncio
async def test_api_governance_service_integration():
    """Verify integration via ServiceLocator."""
    from app.utils.service_locator import ServiceLocator

    svc = ServiceLocator.get_service("api_governance_service")
    assert svc is not None
    assert svc is governance_service
