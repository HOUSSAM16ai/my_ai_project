from enum import StrEnum


class AuditAction(StrEnum):
    """
    Standardized audit actions to ensure high-precision tracking.
    """

    # Auth Actions
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    TOKEN_REFRESH = "token_refresh"

    # User Management
    CREATE_USER = "create_user"
    UPDATE_USER = "update_user"
    DELETE_USER = "delete_user"
    RESET_PASSWORD = "reset_password"

    # System/Policy
    UPDATE_POLICY = "update_policy"
    SYSTEM_CONFIG_CHANGE = "system_config_change"

    # Procedural AI & Fraud Detection
    PROCEDURAL_AUDIT = "procedural_audit"
    FRAUD_ALERT = "fraud_alert"
    COMPLIANCE_CHECK = "compliance_check"

    # Generic
    ACCESS = "access"
    MODIFY = "modify"
    DELETE = "delete"
