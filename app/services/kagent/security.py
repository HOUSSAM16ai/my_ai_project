"""
Kagent Security Mesh.
---------------------
Simulates mTLS and Access Control Lists (ACL) for inter-agent communication.
Ensures only authorized nodes can invoke sensitive services.
"""

from app.core.logging import get_logger

logger = get_logger("kagent-security")


class SecurityMesh:
    """
    شبكة الأمان (Security Mesh).
    تتحقق من الهوية والصلاحيات قبل السماح بتنفيذ الإجراء.
    """

    # قائمة افتراضية بالرموز الموثوقة (لأغراض المحاكاة)
    TRUSTED_TOKENS = {"supervisor-sys-key", "test-runner-key", "internal-mesh-key"}

    # قائمة التحكم بالوصول (ACL)
    # Caller -> Allowed Services
    ACL = {
        "supervisor": ["reasoning_engine", "researcher", "writer", "auditor"],
        "super_reasoner": ["search_engine", "reasoning_engine"],
        "test_runner": ["*"],
    }

    def verify_access(self, caller_id: str, target_service: str, token: str | None) -> bool:
        """
        التحقق من صلاحية الوصول (Access Verification).
        1. التحقق من التوكن.
        2. التحقق من الـ ACL.
        """
        # 1. Token Check (Simulated mTLS)
        if not token or token not in self.TRUSTED_TOKENS:
            logger.warning(f"⛔ Security Alert: Invalid token from {caller_id}")
            return False

        # 2. ACL Check
        allowed_targets = self.ACL.get(caller_id, [])
        if "*" in allowed_targets:
            return True

        if target_service not in allowed_targets:
            logger.warning(f"⛔ Access Denied: {caller_id} cannot access {target_service}")
            return False

        return True
