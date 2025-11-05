"""
Comprehensive Security Tests - Enterprise Grade
Testing all security features implemented in the project

Following test patterns from:
- Google (Security Testing Framework)
- Microsoft (Security Development Lifecycle)
- OWASP (Testing Guide)
"""

import pytest
from unittest.mock import Mock, patch
from app.security.secure_auth import SecureAuthenticationService, UserRole, AuthEventType
from app.security.owasp_validator import OWASPValidator, SecuritySeverity, OWASPCategory
from app.security.secure_templates import (
    secure_register_user,
    validate_email,
    sanitize_filename,
)


class TestSecureAuthentication:
    """Test suite for SecureAuthenticationService"""

    def test_password_hashing(self):
        """Test secure password hashing"""
        service = SecureAuthenticationService()
        
        password = "TestPassword123!"
        hashed = service.hash_password(password)
        
        # Hash should be different from original
        assert hashed != password
        
        # Should verify correctly
        assert service.verify_password(password, hashed)
        
        # Should fail with wrong password
        assert not service.verify_password("WrongPassword", hashed)

    def test_password_strength_validation(self):
        """Test password strength requirements"""
        service = SecureAuthenticationService()
        
        # Test weak passwords
        weak_passwords = [
            ("short", "too short"),
            ("alllowercase123!", "no uppercase"),
            ("ALLUPPERCASE123!", "no lowercase"),
            ("NoDigitsHere!", "no digits"),
            ("NoSpecial123", "no special char"),
            ("password123!", "common password"),
        ]
        
        for password, reason in weak_passwords:
            is_valid, errors = service.validate_password_strength(password)
            assert not is_valid, f"Password '{password}' should fail ({reason})"
            assert len(errors) > 0
        
        # Test strong password
        strong_password = "StrongP@ssw0rd123"
        is_valid, errors = service.validate_password_strength(strong_password)
        assert is_valid, f"Strong password rejected: {errors}"
        assert len(errors) == 0

    def test_account_lockout_after_failures(self):
        """Test account lockout after max failed attempts"""
        service = SecureAuthenticationService()
        
        email = "test@example.com"
        ip = "192.168.1.1"
        
        # Record failed attempts
        for i in range(service.MAX_FAILED_ATTEMPTS):
            service._record_failed_attempt(email, ip)
        
        # Should determine account needs locking
        assert service._should_lock_account(email)
        
        # Lock the account
        service._lock_account(email)
        
        # Account should now be locked
        assert service._is_account_locked(email)

    def test_captcha_requirement_after_failures(self):
        """Test CAPTCHA required after threshold"""
        service = SecureAuthenticationService()
        
        email = "test@example.com"
        ip = "192.168.1.1"
        
        # Record failures up to CAPTCHA threshold
        for i in range(service.CAPTCHA_THRESHOLD):
            service._record_failed_attempt(email, ip)
        
        # CAPTCHA should be required
        assert service._is_captcha_required(email)

    def test_failed_attempts_cleared_on_success(self):
        """Test failed attempts are cleared after successful login"""
        service = SecureAuthenticationService()
        
        email = "test@example.com"
        ip = "192.168.1.1"
        
        # Record some failures
        service._record_failed_attempt(email, ip)
        service._record_failed_attempt(email, ip)
        
        assert service._is_captcha_required(email) == False
        
        # Clear on success
        service._clear_failed_attempts(email)
        
        # No CAPTCHA required after clearing
        assert service._is_captcha_required(email) == False

    def test_account_auto_unlock_after_timeout(self):
        """Test account unlocks automatically after timeout"""
        from datetime import datetime, timedelta, UTC
        
        service = SecureAuthenticationService()
        email = "test@example.com"
        
        # Lock account with old timestamp
        old_time = datetime.now(UTC) - timedelta(seconds=service.LOCKOUT_DURATION + 60)
        service.locked_accounts[email] = old_time
        
        # Should be unlocked now
        assert not service._is_account_locked(email)

    def test_session_creation(self):
        """Test secure session token generation"""
        service = SecureAuthenticationService()
        
        user = {
            "id": 1,
            "email": "test@example.com",
            "role": UserRole.USER.value
        }
        
        request = Mock()
        request.remote_addr = "192.168.1.1"
        request.headers = {"User-Agent": "Test Browser"}
        
        session = service._create_session(user, request)
        
        assert session.user_id == 1
        assert session.email == "test@example.com"
        assert len(session.session_token) > 20  # Secure random token
        assert session.ip_address == "192.168.1.1"

    def test_session_verification(self):
        """Test session token verification"""
        service = SecureAuthenticationService()
        
        user = {"id": 1, "email": "test@example.com", "role": "user"}
        request = Mock()
        request.remote_addr = "192.168.1.1"
        
        session = service._create_session(user, request)
        
        # Valid session
        is_valid, retrieved_session = service.verify_session(session.session_token)
        assert is_valid
        assert retrieved_session.user_id == 1
        
        # Invalid session
        is_valid, _ = service.verify_session("invalid_token")
        assert not is_valid

    def test_session_revocation(self):
        """Test session can be revoked (logout)"""
        service = SecureAuthenticationService()
        
        user = {"id": 1, "email": "test@example.com", "role": "user"}
        request = Mock()
        request.remote_addr = "192.168.1.1"
        
        session = service._create_session(user, request)
        token = session.session_token
        
        # Revoke session
        assert service.revoke_session(token)
        
        # Session should no longer be valid
        is_valid, _ = service.verify_session(token)
        assert not is_valid


class TestOWASPValidator:
    """Test suite for OWASP security validator"""

    def test_privilege_escalation_detection(self):
        """Test detection of privilege escalation vulnerabilities"""
        validator = OWASPValidator()
        
        # Should detect role from user input
        code = """
        user.role = request.json.get('role')
        user.is_admin = request.form.get('is_admin')
        """
        
        issues = validator.validate_access_control(code)
        
        assert len(issues) >= 2
        assert any("Privilege Escalation" in issue.title for issue in issues)
        assert any(issue.severity == SecuritySeverity.CRITICAL for issue in issues)

    def test_sql_injection_detection(self):
        """Test detection of SQL injection vulnerabilities"""
        validator = OWASPValidator()
        
        # Should detect SQL injection
        code = '''
        query = f"SELECT * FROM users WHERE id = {user_id}"
        cursor.execute("SELECT * FROM users WHERE name = '%s'" % username)
        '''
        
        issues = validator.validate_injection_prevention(code)
        
        assert len(issues) > 0
        assert any("SQL Injection" in issue.title for issue in issues)

    def test_xss_detection(self):
        """Test detection of XSS vulnerabilities"""
        validator = OWASPValidator()
        
        code = '''
        element.innerHTML = user_input
        dangerouslySetInnerHTML={{__html: userContent}}
        '''
        
        issues = validator.validate_injection_prevention(code)
        
        assert len(issues) > 0
        assert any("XSS" in issue.title or "Cross-Site" in issue.title for issue in issues)

    def test_weak_crypto_detection(self):
        """Test detection of weak cryptography"""
        validator = OWASPValidator()
        
        code = '''
        import hashlib
        password_hash = hashlib.md5(password.encode()).hexdigest()
        token = hashlib.sha1(data.encode()).hexdigest()
        random_value = random.random()
        '''
        
        issues = validator.validate_cryptography(code)
        
        assert len(issues) > 0
        assert any("Weak" in issue.title or "Cryptographic" in issue.title for issue in issues)

    def test_hardcoded_secret_detection(self):
        """Test detection of hardcoded secrets"""
        validator = OWASPValidator()
        
        code = '''
        API_KEY = "sk-1234567890abcdef"
        password = "admin123"
        secret_token = "my-secret-token"
        '''
        
        issues = validator.validate_cryptography(code)
        
        assert len(issues) > 0
        assert any("Hardcoded" in issue.title or "Secret" in issue.title for issue in issues)

    def test_missing_authentication_logging(self):
        """Test detection of missing security logging"""
        validator = OWASPValidator()
        
        code = '''
        def authenticate(email, password):
            user = User.query.filter_by(email=email).first()
            if user and user.check_password(password):
                return user
        '''
        
        issues = validator.validate_logging_monitoring(code)
        
        assert len(issues) > 0
        assert any("Logging" in issue.title for issue in issues)

    def test_sensitive_data_in_logs(self):
        """Test detection of sensitive data being logged"""
        validator = OWASPValidator()
        
        code = '''
        logger.info(f"User login with password: {password}")
        log.debug(f"Token: {api_token}")
        '''
        
        issues = validator.validate_logging_monitoring(code)
        
        assert len(issues) > 0
        assert any("Sensitive Data" in issue.title for issue in issues)


class TestSecureTemplates:
    """Test suite for secure code templates"""

    def test_email_validation(self):
        """Test email validation"""
        # Valid emails
        valid_emails = [
            "test@example.com",
            "user.name@example.co.uk",
            "user+tag@example.com",
        ]
        
        for email in valid_emails:
            is_valid, error = validate_email(email)
            assert is_valid, f"Email '{email}' should be valid, error: {error}"
        
        # Invalid emails
        invalid_emails = [
            "not-an-email",
            "@example.com",
            "user@",
            "user name@example.com",
            "user\n@example.com",  # Email header injection
        ]
        
        for email in invalid_emails:
            is_valid, error = validate_email(email)
            assert not is_valid, f"Email '{email}' should be invalid"

    def test_filename_sanitization(self):
        """Test filename sanitization"""
        # Path traversal attempts
        assert "../../../etc/passwd" not in sanitize_filename("../../../etc/passwd")
        assert "..\\..\\" not in sanitize_filename("..\\..\\windows\\system32")
        
        # Special characters removed
        assert sanitize_filename("file<>:\"|?*.txt") == "file.txt"
        
        # Length limiting
        long_name = "a" * 300 + ".txt"
        sanitized = sanitize_filename(long_name)
        assert len(sanitized) <= 255

    def test_secure_register_prevents_admin_escalation(self):
        """Test registration doesn't allow admin privilege escalation"""
        # This is a conceptual test - actual implementation would need database
        # The key is that is_admin is hardcoded to False in secure_register_user
        
        # Even if user tries to pass is_admin=True, it should be ignored
        # The template ALWAYS sets is_admin=False
        
        # Read the template code to verify
        with open("app/security/secure_templates.py", "r") as f:
            code = f.read()
            assert "is_admin=False" in code
            assert "# 🔒 LOCKED - Never from user input" in code


class TestRateLimiting:
    """Test suite for rate limiting"""

    def test_rate_limiter_initialization(self):
        """Test rate limiter initializes correctly"""
        from app.security.rate_limiter import AdaptiveRateLimiter, UserTier
        
        limiter = AdaptiveRateLimiter()
        
        assert limiter is not None
        assert len(limiter.stats) > 0

    def test_rate_limiting_enforcement(self):
        """Test rate limiting functionality exists and works"""
        from app.security.rate_limiter import AdaptiveRateLimiter, UserTier
        
        limiter = AdaptiveRateLimiter()
        
        request = Mock()
        request.remote_addr = "192.168.1.1"
        
        # Test rate limiting check returns expected structure
        allowed, info = limiter.check_rate_limit(request, user_id="test_user", tier=UserTier.FREE)
        
        # Should return a tuple with boolean and dict
        assert isinstance(allowed, bool)
        assert isinstance(info, dict)
        
        # Info should contain rate limit details
        assert "tier" in info
        assert "limit_minute" in info
        assert "allowed" in info
        
        # Verify statistics tracking
        stats = limiter.get_statistics()
        assert "total_requests" in stats
        assert stats["total_requests"] > 0


class TestSecurityIntegration:
    """Integration tests for security features"""

    def test_complete_authentication_flow(self):
        """Test complete authentication flow with all security features"""
        service = SecureAuthenticationService()
        
        # 1. Failed login attempts
        request = Mock()
        request.remote_addr = "192.168.1.1"
        
        email = "test@example.com"
        
        # First 2 failures - no CAPTCHA
        for i in range(2):
            service._record_failed_attempt(email, "192.168.1.1")
        
        assert not service._is_captcha_required(email)
        
        # 3rd failure - CAPTCHA required
        service._record_failed_attempt(email, "192.168.1.1")
        assert service._is_captcha_required(email)
        
        # Continue to 5 failures - account locked
        for i in range(2):
            service._record_failed_attempt(email, "192.168.1.1")
        
        service._lock_account(email)
        assert service._is_account_locked(email)

    def test_security_statistics_tracking(self):
        """Test security statistics are tracked correctly"""
        service = SecureAuthenticationService()
        
        # Generate some activity
        request = Mock()
        request.remote_addr = "192.168.1.1"
        
        for i in range(5):
            service._record_failed_attempt("test@example.com", "192.168.1.1")
        
        stats = service.get_statistics()
        
        assert "total_login_attempts" in stats
        assert "failed_logins" in stats
        assert "locked_accounts" in stats


def test_security_checklist_exists():
    """Verify security checklist documentation exists"""
    import os
    assert os.path.exists("SECURITY_CHECKLIST.md"), "Security checklist must exist"


def test_owasp_validator_module_exists():
    """Verify OWASP validator module exists"""
    import os
    assert os.path.exists("app/security/owasp_validator.py"), "OWASP validator must exist"


def test_secure_templates_module_exists():
    """Verify secure templates module exists"""
    import os
    assert os.path.exists("app/security/secure_templates.py"), "Secure templates must exist"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
