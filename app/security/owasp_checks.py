"""واجهات فحوصات OWASP المجمعة وتسجيلها كبيانات قابلة للتوسعة."""

from collections.abc import Callable

from app.security.owasp_checks_access import check_access_control_issues
from app.security.owasp_checks_auth import check_authentication_issues
from app.security.owasp_checks_crypto import check_cryptography_issues
from app.security.owasp_checks_injection import check_injection_issues
from app.security.owasp_checks_logging import check_logging_issues
from app.security.owasp_checks_session import check_session_issues
from app.security.owasp_models import SecurityIssue

type CheckFunction = Callable[[str, str], list[SecurityIssue]]

CHECK_PIPELINE: list[CheckFunction] = [
    check_authentication_issues,
    check_access_control_issues,
    check_injection_issues,
    check_cryptography_issues,
    check_session_issues,
    check_logging_issues,
]

__all__ = [
    "check_access_control_issues",
    "check_authentication_issues",
    "check_cryptography_issues",
    "check_injection_issues",
    "check_logging_issues",
    "check_session_issues",
    "CHECK_PIPELINE",
    "CheckFunction",
]
