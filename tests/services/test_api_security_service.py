# tests/services/test_api_security_service.py
"""
اختبارات خدمة أمان الواجهة البرمجية.

يتحقق هذا الملف من إنشاء وتكامل خدمة الأمان (SuperhumanSecuritySystem).
تم تحديثه ليتوافق مع معايير Dependency Injection بدلاً من ServiceLocator القديم.
"""

import pytest

from app.services.api.api_security_service import (
    SuperhumanSecuritySystem,
    get_security_service,
    security_service,
)


def test_api_security_service_instantiation():
    """Test that the security service is instantiated correctly."""
    assert security_service is not None
    assert isinstance(security_service, SuperhumanSecuritySystem)
    assert get_security_service() is security_service


def test_security_service_methods():
    """Test basic method availability."""
    # Updated to match new facade interface (SuperhumanSecuritySystem)
    assert hasattr(security_service, "analyze_event")
    assert hasattr(security_service, "get_recent_threats")


@pytest.mark.asyncio
async def test_api_security_service_di():
    """
    Verify integration via Dependency Injection conventions.

    This replaces the old ServiceLocator test.
    """
    # In the new architecture, we rely on the `security_service` singleton
    # or dependency injection providers.
    svc = get_security_service()
    assert svc is not None
    assert svc is security_service
