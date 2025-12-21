# tests/test_security_enterprise.py

from app.security.secure_auth import SecureAuthenticationService


class TestSecureAuthentication:
    def test_password_hashing(self):
        service = SecureAuthenticationService()
        password = "TestPassword123!"
        hashed = service.hash_password(password)
        assert hashed != password
        assert service.verify_password(password, hashed)
        assert not service.verify_password("WrongPassword", hashed)
