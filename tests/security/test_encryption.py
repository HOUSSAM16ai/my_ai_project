# tests/security/test_encryption.py
import pytest
from app.security.encryption import QuantumSafeEncryption

def test_encryption_decryption():
    """Test basic encryption and decryption"""
    encryption = QuantumSafeEncryption()
    data = b"test data"
    encrypted_data, key_id = encryption.encrypt(data)
    decrypted_data = encryption.decrypt(encrypted_data, key_id)
    assert data == decrypted_data

def test_decryption_with_invalid_key_id():
    """Test decryption with an invalid key ID"""
    encryption = QuantumSafeEncryption()
    data = b"test data"
    encrypted_data, _ = encryption.encrypt(data)
    with pytest.raises(ValueError):
        encryption.decrypt(encrypted_data, "invalid_key_id")

def test_key_rotation():
    """Test key rotation"""
    encryption = QuantumSafeEncryption()
    old_key_id = encryption.current_key_id
    encryption.rotate_keys()
    new_key_id = encryption.current_key_id
    assert old_key_id != new_key_id

def test_get_statistics():
    """Test the get_statistics method"""
    encryption = QuantumSafeEncryption()
    stats = encryption.get_statistics()
    assert stats["total_keys"] == 1
    assert stats["current_key_id"] is not None
    assert stats["oldest_key"] is not None
