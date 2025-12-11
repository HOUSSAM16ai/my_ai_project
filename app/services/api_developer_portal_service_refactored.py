# app/services/api_developer_portal_service.py
"""
API Developer Portal Service - LEGACY COMPATIBILITY
==================================================
This file delegates to the refactored developer_portal module.

Original file: 784+ lines
Refactored: Delegates to developer_portal/ module following Hexagonal Architecture

For new code, import from: app.services.developer_portal
"""

# Legacy imports for backward compatibility
from app.services.developer_portal.domain import (
    APIKey,
    APIKeyStatus,
    CodeExample,
    SDKLanguage,
    SDKPackage,
    SupportTicket,
    TicketPriority,
    TicketStatus,
)

# Placeholder for facade - will delegate to application layer services
# from app.services.developer_portal.facade import (
#     DeveloperPortalService,
#     get_developer_portal_service,
# )


class DeveloperPortalService:
    """Developer Portal Service - Backward Compatible Stub"""

    def __init__(self):
        import warnings

        warnings.warn(
            "DeveloperPortalService is using legacy implementation. "
            "Full hexagonal refactoring in progress at app/services/developer_portal/",
            DeprecationWarning,
            stacklevel=2,
        )


def get_developer_portal_service() -> DeveloperPortalService:
    """Get singleton instance of developer portal service"""
    return DeveloperPortalService()


# Re-export everything for backward compatibility
__all__ = [
    # Enums
    "SDKLanguage",
    "TicketStatus",
    "TicketPriority",
    "APIKeyStatus",
    # Models
    "APIKey",
    "SupportTicket",
    "SDKPackage",
    "CodeExample",
    # Service
    "DeveloperPortalService",
    "get_developer_portal_service",
]
