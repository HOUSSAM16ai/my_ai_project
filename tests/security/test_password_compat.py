from passlib.context import CryptContext

from app.models import pwd_context


def test_legacy_hash_support():
    # Test that pwd_context supports legacy schemes
    assert "sha256_crypt" in pwd_context.schemes()
    assert "pbkdf2_sha256" in pwd_context.schemes()
    assert "bcrypt" in pwd_context.schemes()

    # Simulate a legacy hash (sha256_crypt)
    # Example hash: $5$rounds=535000$....
    # Actually, let's use a known hash if possible, or just check the config.
    # We can check if `verify` works for a mock legacy hash if we can generate one.

    # Generate a legacy hash
    legacy_ctx = CryptContext(schemes=["sha256_crypt"])
    password = "testpassword"
    legacy_hash = legacy_ctx.hash(password)

    # Verify using the main pwd_context
    assert pwd_context.verify(password, legacy_hash)

    # Check that it wants to update (if deprecated="auto" is working and schemes order prefers argon2/bcrypt)
    # Note: Argon2 is usually default if first.
    assert pwd_context.needs_update(legacy_hash)

    # Verify new hash generation (should be argon2 or bcrypt)
    new_hash = pwd_context.hash(password)
    assert pwd_context.verify(password, new_hash)
    assert not pwd_context.needs_update(new_hash)
