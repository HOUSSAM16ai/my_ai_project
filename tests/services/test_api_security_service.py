# tests/services/test_api_security_service.py
import pytest
from app.services.api_security_service import get_security_service, security_service, SuperhumanSecuritySystem

def test_api_security_service_instantiation():
    """Test that the security service is instantiated correctly."""
    assert security_service is not None
    assert isinstance(security_service, SuperhumanSecuritySystem)
    assert get_security_service() is security_service

def test_security_service_methods():
    """Test basic method availability."""
    assert hasattr(security_service, "process_request")
    assert hasattr(security_service, "get_security_dashboard")

@pytest.mark.asyncio
async def test_api_security_service_integration():
    """Verify integration via ServiceLocator."""
    from app.utils.service_locator import ServiceLocator

    svc = ServiceLocator.get_service("api_security_service")
    assert svc is not None
    assert svc is security_service
