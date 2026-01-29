from app.core.domain.models import User


class TestUserModel:
    """Tests for User model."""

    def test_user_creation(self):
        """User can be created with required fields."""
        user = User(full_name="Test User", email="test@example.com")
        assert user.full_name == "Test User"
        assert user.email == "test@example.com"
        assert user.is_admin is False
        assert user.password_hash is None

    def test_set_password(self):
        """set_password hashes the password."""
        user = User(full_name="Test", email="test@example.com")
        user.set_password("secure_password_123")
        assert user.password_hash is not None
        assert user.password_hash != "secure_password_123"
        assert len(user.password_hash) > 20

    def test_check_password_correct(self):
        """check_password returns True for correct password."""
        user = User(full_name="Test", email="test@example.com")
        user.set_password("my_password")
        assert user.check_password("my_password") is True

    def test_check_password_incorrect(self):
        """check_password returns False for incorrect password."""
        user = User(full_name="Test", email="test@example.com")
        user.set_password("my_password")
        assert user.check_password("wrong_password") is False

    def test_check_password_no_hash(self):
        """check_password returns False when no hash is set."""
        user = User(full_name="Test", email="test@example.com")
        assert user.check_password("any_password") is False

    def test_verify_password_alias(self):
        """verify_password is an alias for check_password."""
        user = User(full_name="Test", email="test@example.com")
        user.set_password("my_password")
        assert user.verify_password("my_password") is True
        assert user.verify_password("wrong") is False

    def test_user_repr(self):
        """User has meaningful repr."""
        user = User(id=1, full_name="Test", email="test@example.com")
        repr_str = repr(user)
        assert "User" in repr_str
        assert "1" in repr_str
        assert "test@example.com" in repr_str

    def test_password_hashing_uses_argon2(self):
        """Password hashing prefers Argon2."""
        user = User(full_name="Test", email="test@example.com")
        user.set_password("test123")
        # Argon2 hashes start with $argon2
        assert user.password_hash.startswith("$argon2")


class TestPasswordHashingEdgeCases:
    """Edge case tests for password hashing."""

    def test_empty_password(self):
        """Empty password can be hashed and verified."""
        user = User(full_name="Test", email="test@example.com")
        user.set_password("")
        assert user.check_password("") is True
        assert user.check_password("not_empty") is False

    def test_unicode_password(self):
        """Unicode characters in password work correctly."""
        user = User(full_name="Test", email="test@example.com")
        user.set_password("كلمة_سر_قوية_🔐")
        assert user.check_password("كلمة_سر_قوية_🔐") is True
        assert user.check_password("wrong") is False

    def test_very_long_password(self):
        """Very long passwords work correctly."""
        user = User(full_name="Test", email="test@example.com")
        long_password = "a" * 1000
        user.set_password(long_password)
        assert user.check_password(long_password) is True

    def test_special_characters_password(self):
        """Special characters in password work correctly."""
        user = User(full_name="Test", email="test@example.com")
        special_password = "p@$$w0rd!#$%^&*()_+-=[]{}|;':\",./<>?"
        user.set_password(special_password)
        assert user.check_password(special_password) is True
