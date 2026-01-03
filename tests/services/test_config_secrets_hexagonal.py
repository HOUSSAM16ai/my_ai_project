
import pytest

from app.services.api_config_secrets.service import (
    ConfigSecretsService,
    Environment,
    SecretType,
    get_config_secrets_service,
)


@pytest.fixture
def service():
    return ConfigSecretsService()

def test_config_crud(service):
    """Test Create, Read for Configuration"""
    service.set_config(
        Environment.DEVELOPMENT, "test_key", "test_value", "A test config"
    )
    val = service.get_config(Environment.DEVELOPMENT, "test_key")
    assert val == "test_value"

    # Test default
    assert service.get_config(Environment.DEVELOPMENT, "missing", "default") == "default"

def test_secret_lifecycle(service):
    """Test Create, Read, Rotate for Secrets"""
    secret_id = service.create_secret(
        "api_key_v1", "secret-123", SecretType.API_KEY, Environment.DEVELOPMENT
    )
    assert secret_id is not None

    # Read
    val = service.get_secret(secret_id)
    assert val == "secret-123"

    # Rotate
    success = service.rotate_secret(secret_id, "secret-456")
    assert success is True

    val_new = service.get_secret(secret_id)
    assert val_new == "secret-456"

def test_audit_logs(service):
    """Test that actions generate audit logs"""
    service.create_secret(
        "audit_test", "123", SecretType.API_KEY, Environment.DEVELOPMENT
    )
    logs = service.get_audit_report()
    assert len(logs) > 0
    assert logs[-1]['action'] == 'write'

def test_singleton():
    """Test singleton accessor"""
    s1 = get_config_secrets_service()
    s2 = get_config_secrets_service()
    assert s1 is s2
