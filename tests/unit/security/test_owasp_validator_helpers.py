"""اختبارات وحدات لوظائف OWASP Validator المساعدة."""
import re

from app.security.owasp_validator import (
    OWASPValidator,
    OWASPCategory,
    SecuritySeverity,
)


def test_check_weak_password_hashing_detects_risky_usage() -> None:
    validator = OWASPValidator()
    code = """
    user_password = request.form.get('password')
    hashed = hashlib.md5(user_password.encode())
    """

    issues = validator._check_weak_password_hashing(code, "auth.py")

    assert len(issues) == 1
    issue = issues[0]
    assert issue.category is OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES
    assert issue.severity is SecuritySeverity.CRITICAL
    assert issue.file_path == "auth.py"


def test_check_weak_password_hashing_skips_non_security_usage() -> None:
    validator = OWASPValidator()
    code = (
        "token = hashlib.md5(user.email.encode()).hexdigest()[:8]\n"
        "slug = hashlib.md5(page.slug.encode(), usedforsecurity=False)"
    )

    issues = validator._check_weak_password_hashing(code, "identifiers.py")

    assert issues == []


def test_check_weak_password_hashing_ignores_non_password_context() -> None:
    validator = OWASPValidator()
    code = "identifier = hashlib.md5(customer.id.encode()).hexdigest()"

    assert validator._check_weak_password_hashing(code, "ids.py") == []


def test_check_hardcoded_secrets_filters_safe_sources() -> None:
    validator = OWASPValidator()
    env_configured = (
        "api_key = os.getenv('API_KEY')\n"
        "password = settings.credentials['password']\n"
        "# api_key = 'should_ignore_mock'"
    )

    safe_issues = validator._check_hardcoded_secrets(env_configured, "config.py")

    assert safe_issues == []


def test_check_hardcoded_secrets_ignores_comments() -> None:
    validator = OWASPValidator()
    commented_secret = "# password = 'should_not_trigger'"

    issues = validator._check_hardcoded_secrets(commented_secret, "config.py")

    assert issues == []


def test_check_hardcoded_secrets_skips_enum_markers() -> None:
    validator = OWASPValidator()
    code = "class SecretKeys(Enum):\n    API_KEY = 'placeholder'"

    assert validator._check_hardcoded_secrets(code, "constants.py") == []


def test_check_hardcoded_secrets_skips_test_files() -> None:
    validator = OWASPValidator()
    code = "token = 'fixture-secret'"

    issues = validator._check_hardcoded_secrets(code, "test_helpers.py")

    assert issues == []


def test_check_hardcoded_secrets_detects_literal_credentials() -> None:
    validator = OWASPValidator()
    code = """
    password = 'super-secret-password'
    token = 'sk_test_123'
    """

    issues = validator._check_hardcoded_secrets(code, "secrets.py")

    assert len(issues) == 2
    assert all(issue.severity is SecuritySeverity.CRITICAL for issue in issues)
    assert all(issue.category is OWASPCategory.A05_SECURITY_MISCONFIGURATION for issue in issues)


def test_command_injection_detection() -> None:
    validator = OWASPValidator()
    code = """
    def unsafe(command: str):
        os.system(command)
    """

    issues = validator._check_command_injection(code, "executor.py")

    assert len(issues) == 1
    assert issues[0].title == "Potential Command Injection"


def test_command_injection_ignores_safe_subprocess_usage() -> None:
    validator = OWASPValidator()
    code = (
        "import subprocess\n"
        "subprocess.call(['ls'])\n"
        "subprocess.run(['echo', 'ok'], shell=False)"
    )

    issues = validator._check_command_injection(code, "executor.py")

    assert issues == []


def test_plaintext_password_storage_detects_unhashed_input() -> None:
    validator = OWASPValidator()
    code = "password = request.form.get('password')\nuser.save(password)"

    issues = validator._check_plaintext_password_storage(code, "auth.py")

    assert len(issues) == 1
    assert issues[0].category is OWASPCategory.A02_CRYPTOGRAPHIC_FAILURES


def test_plaintext_password_storage_ignores_hashed_flow() -> None:
    validator = OWASPValidator()
    code = (
        "password = request.form['password']\n"
        "hashed = hashlib.sha256(password.encode()).hexdigest()\n"
        "user.password = hashed"
    )

    assert validator._check_plaintext_password_storage(code, "auth.py") == []


def test_authentication_rate_limiting_missing_warning() -> None:
    validator = OWASPValidator()
    code = "def login():\n    return login_user()"

    issues = validator._check_authentication_rate_limiting(code, "views.py")

    assert len(issues) == 1
    assert issues[0].severity is SecuritySeverity.HIGH


def test_authentication_rate_limiting_silenced_when_present() -> None:
    validator = OWASPValidator()
    code = "def login():\n    return login_user(rate_limit=True)"

    assert validator._check_authentication_rate_limiting(code, "views.py") == []


def test_role_and_admin_escalation_detection() -> None:
    validator = OWASPValidator()
    code = (
        "role = request.json.get('role')\n"
        "is_admin = request.form.get('is_admin')"
    )

    role_issues = validator._check_role_escalation(code, "access.py")
    admin_issues = validator._check_admin_escalation(code, "access.py")

    assert len(role_issues) == 1
    assert len(admin_issues) == 1
    assert role_issues[0].category is OWASPCategory.A01_BROKEN_ACCESS_CONTROL
    assert admin_issues[0].category is OWASPCategory.A01_BROKEN_ACCESS_CONTROL


def test_missing_auth_checks_detected_for_user_route() -> None:
    validator = OWASPValidator()
    code = "@app.route('/users/<int:user_id>')\ndef get_user(user_id):\n    return 'ok'"

    issues = validator._check_missing_auth_checks(code, "routes.py")

    assert len(issues) == 1
    assert issues[0].title == "Missing Authorization Check"


def test_missing_auth_checks_skipped_when_protected() -> None:
    validator = OWASPValidator()
    code = (
        "@login_required\n"
        "@app.route('/users/<int:user_id>')\n"
        "def get_user(user_id):\n    return 'ok'"
    )

    assert validator._check_missing_auth_checks(code, "routes.py") == []


def test_sql_injection_detection_and_safe_path() -> None:
    validator = OWASPValidator()
    vulnerable = "cursor.execute(\"SELECT * FROM users WHERE id = %s\" % user_id)"
    safe = "User.objects.filter(id=user_id).first()"

    vulnerable_issues = validator._check_sql_injection(vulnerable, "db.py")
    safe_issues = validator._check_sql_injection(safe, "db.py")

    assert len(vulnerable_issues) == 1
    assert vulnerable_issues[0].cwe_id == "CWE-89"
    assert safe_issues == []


def test_xss_detection_flags_dangerous_html_usage() -> None:
    validator = OWASPValidator()
    code = "element.innerHTML = request.args.get('content')"

    issues = validator._check_xss_vulnerabilities(code, "ui.js")

    assert len(issues) == 1
    assert issues[0].severity is SecuritySeverity.HIGH


def test_weak_crypto_detection_and_false_positives() -> None:
    validator = OWASPValidator()
    insecure = "hashlib.sha1(b'data').hexdigest()"
    ignored = "import hashlib\nvalue = hashlib.md5(b'data').hexdigest()"
    non_crypto_use = "hashlib.md5(b'data', usedforsecurity=False).hexdigest()"

    insecure_issues = validator._check_weak_crypto_algorithms(insecure, "crypto.py")
    ignored_issues = validator._check_weak_crypto_algorithms(ignored, "crypto.py")
    non_crypto_issues = validator._check_weak_crypto_algorithms(non_crypto_use, "crypto.py")

    assert len(insecure_issues) == 1
    assert insecure_issues[0].severity is SecuritySeverity.MEDIUM
    assert ignored_issues == []
    assert non_crypto_issues == []


def test_cookie_flag_validations() -> None:
    validator = OWASPValidator()
    code = (
        "SESSION_COOKIE_SECURE = False\n"
        "SESSION_COOKIE_HTTPONLY = False\n"
    )

    secure_issues = validator._check_secure_cookie_flag(code, "settings.py")
    httponly_issues = validator._check_httponly_cookie_flag(code, "settings.py")

    assert len(secure_issues) == 1
    assert len(httponly_issues) == 1
    assert secure_issues[0].cwe_id == "CWE-614"
    assert httponly_issues[0].cwe_id == "CWE-1004"


def test_cookie_flag_validations_skip_when_already_secure() -> None:
    validator = OWASPValidator()
    code = (
        "SESSION_COOKIE_SECURE = True\n"
        "SESSION_COOKIE_HTTPONLY = True\n"
    )

    secure_issues = validator._check_secure_cookie_flag(code, "settings.py")
    httponly_issues = validator._check_httponly_cookie_flag(code, "settings.py")

    assert secure_issues == []
    assert httponly_issues == []


def test_logging_validations_for_missing_and_sensitive_events() -> None:
    validator = OWASPValidator()
    missing = "def authenticate_user():\n    return authenticate(user)"
    sensitive = "logger.info('password: %s', password)"
    instrumented = "def login():\n    logger.info('auth attempt')\n    return authenticate(user)"

    missing_issues = validator._check_missing_auth_logging(missing, "logs.py")
    sensitive_issues = validator._check_sensitive_logging(sensitive, "logs.py")
    instrumented_issues = validator._check_missing_auth_logging(instrumented, "logs.py")

    assert len(missing_issues) == 1
    assert len(sensitive_issues) == 1
    assert instrumented_issues == []


def test_is_false_positive_crypto_respects_context_markers() -> None:
    validator = OWASPValidator()
    non_security = "token = hashlib.md5(b'data', usedforsecurity=False).hexdigest()"
    import_only = "import hashlib\nvalue = hashlib.sha1(b'data').hexdigest()"
    actual_issue = "hashlib.sha1(b'secret').hexdigest()"

    non_security_match = re.search(validator.insecure_crypto_patterns[0], non_security)
    import_match = re.search(validator.insecure_crypto_patterns[1], import_only)
    actual_match = re.search(validator.insecure_crypto_patterns[1], actual_issue)

    assert non_security_match is not None
    assert import_match is not None
    assert actual_match is not None

    assert validator._is_false_positive_crypto(non_security, non_security_match) is True
    assert validator._is_false_positive_crypto(import_only, import_match) is True
    assert validator._is_false_positive_crypto(actual_issue, actual_match) is False


def test_is_false_positive_secret_detects_env_and_real_literals() -> None:
    validator = OWASPValidator()
    env_configured = "password = 'placeholder'\npassword = os.getenv('DB_PASSWORD', password)"
    literal_secret = "api_key = 'sk_live_123'"

    env_match = re.search(validator.hardcoded_secrets_patterns[0], env_configured, re.IGNORECASE)
    literal_match = re.search(validator.hardcoded_secrets_patterns[1], literal_secret, re.IGNORECASE)

    assert env_match is not None
    assert literal_match is not None

    assert validator._is_false_positive_secret(env_configured, env_match, "settings.py") is True
    assert validator._is_false_positive_secret(literal_secret, literal_match, "service.py") is False
