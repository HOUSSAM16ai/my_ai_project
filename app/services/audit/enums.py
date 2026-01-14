from enum import Enum


class AuditAction(str, Enum):
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

    # Generic
    ACCESS = "access"
    MODIFY = "modify"
    DELETE = "delete"
