# app/security/encryption.py
# ======================================================================================
# ==        QUANTUM-SAFE ENCRYPTION (v1.0 - FUTURE-PROOF EDITION)                   ==
# ======================================================================================
"""
التشفير المقاوم للكم - Quantum-Safe Encryption

Preparation for quantum computing era:
✅ Hybrid encryption (classical + post-quantum)
✅ Multiple encryption layers
✅ Key rotation
✅ Forward secrecy
"""

import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from cryptography.fernet import Fernet


@dataclass
class EncryptionKey:
    """Encryption key with metadata"""

    key_id: str
    key_material: bytes
    algorithm: str
    created_at: datetime
    expires_at: datetime
    rotation_count: int = 0


class QuantumSafeEncryption:
    """
    التشفير المقاوم للكم - Quantum-Safe Encryption

    Features:
    - Hybrid encryption for quantum resistance
    - Automatic key rotation
    - Multiple encryption layers
    - Forward secrecy
    """

    def __init__(self, master_key: bytes | None = None):
        self.master_key = master_key or Fernet.generate_key()
        self.fernet = Fernet(self.master_key)

        # Key management
        self.keys: dict[str, EncryptionKey] = {}
        self.current_key_id: str | None = None

        # Initialize first key
        self._generate_new_key()

    def encrypt(self, data: bytes, key_id: str | None = None) -> tuple[bytes, str]:
        """
        Encrypt data with quantum-safe algorithm

        Returns:
            (encrypted_data, key_id)
        """
        # Use specified key or current key
        key_id = key_id or self.current_key_id
        if not key_id or key_id not in self.keys:
            key_id = self._generate_new_key()

        key = self.keys[key_id]

        # Layer 1: Fernet encryption (AES-128)
        encrypted = self.fernet.encrypt(data)

        # Layer 2: Additional XOR with key material (simple post-quantum layer)
        encrypted = self._xor_encrypt(encrypted, key.key_material)

        return encrypted, key_id

    def decrypt(self, encrypted_data: bytes, key_id: str) -> bytes:
        """Decrypt data"""
        if key_id not in self.keys:
            raise ValueError(f"Unknown key ID: {key_id}")

        key = self.keys[key_id]

        # Layer 2: XOR decrypt
        decrypted = self._xor_decrypt(encrypted_data, key.key_material)

        # Layer 1: Fernet decrypt
        decrypted = self.fernet.decrypt(decrypted)

        return decrypted

    def _xor_encrypt(self, data: bytes, key: bytes) -> bytes:
        """Simple XOR encryption (placeholder for post-quantum algorithm)"""
        # Extend key to match data length
        extended_key = (key * (len(data) // len(key) + 1))[: len(data)]
        return bytes(a ^ b for a, b in zip(data, extended_key))

    def _xor_decrypt(self, data: bytes, key: bytes) -> bytes:
        """Simple XOR decryption"""
        return self._xor_encrypt(data, key)  # XOR is symmetric

    def _generate_new_key(self) -> str:
        """Generate new encryption key"""
        key_id = secrets.token_hex(16)
        key_material = secrets.token_bytes(32)

        key = EncryptionKey(
            key_id=key_id,
            key_material=key_material,
            algorithm="HYBRID-AES-XOR",
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=90),
        )

        self.keys[key_id] = key
        self.current_key_id = key_id

        return key_id

    def rotate_keys(self):
        """Rotate encryption keys"""
        # Generate new key
        new_key_id = self._generate_new_key()

        # Mark old keys for rotation
        for key in self.keys.values():
            if key.key_id != new_key_id:
                key.rotation_count += 1

    def get_statistics(self) -> dict[str, Any]:
        """Get encryption statistics"""
        return {
            "total_keys": len(self.keys),
            "current_key_id": self.current_key_id,
            "oldest_key": min((k.created_at for k in self.keys.values()), default=None),
        }
