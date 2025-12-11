# app/services/developer_portal/__init__.py
"""
Developer Portal Module - Hexagonal Architecture
================================================
Refactored from api_developer_portal_service.py (784 lines)

Architecture:
- domain/: Pure business logic (models, ports)
- application/: Use cases and business workflows
- infrastructure/: External adapters (repositories)
- facade.py: Backward-compatible API
"""

# Domain exports
from app.services.developer_portal.domain.models import (
    APIKey,
    APIKeyStatus,
    CodeExample,
    SDKLanguage,
    SDKPackage,
    SupportTicket,
    TicketPriority,
    TicketStatus,
)

# Application exports
from app.services.developer_portal.application import (
    APIKeyManager,
    TicketManager,
    SDKGenerator,
    CodeExampleManager,
)

# Infrastructure exports
from app.services.developer_portal.infrastructure import (
    InMemoryAPIKeyRepository,
    InMemoryTicketRepository,
    InMemorySDKRepository,
    InMemoryCodeExampleRepository,
)

# Facade exports
from app.services.developer_portal.facade import (
    DeveloperPortalService,
    get_developer_portal_service,
)

__all__ = [
    # Domain models
    "APIKey",
    "APIKeyStatus",
    "CodeExample",
    "SDKLanguage",
    "SDKPackage",
    "SupportTicket",
    "TicketPriority",
    "TicketStatus",
    # Application services
    "APIKeyManager",
    "TicketManager",
    "SDKGenerator",
    "CodeExampleManager",
    # Infrastructure
    "InMemoryAPIKeyRepository",
    "InMemoryTicketRepository",
    "InMemorySDKRepository",
    "InMemoryCodeExampleRepository",
    # Facade
    "DeveloperPortalService",
    "get_developer_portal_service",
]
