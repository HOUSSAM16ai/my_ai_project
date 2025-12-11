# app/services/api_developer_portal_service.py
"""
API Developer Portal Service - LEGACY COMPATIBILITY SHIM
========================================================
This file maintains backward compatibility by delegating to the refactored
hexagonal architecture in app/services/developer_portal/

Original file: 784 lines
Refactored: Delegates to developer_portal/ module

SOLID PRINCIPLES APPLIED:
  - Single Responsibility: Each component has one clear purpose
  - Open/Closed: Open for extension via ports/adapters
  - Liskov Substitution: All implementations are interchangeable
  - Interface Segregation: Small focused protocols
  - Dependency Inversion: Depends on abstractions (ports)

For new code, import from: app.services.developer_portal
This shim exists for backward compatibility only.
"""

from __future__ import annotations

# Re-export everything from the refactored hexagonal architecture
from app.services.developer_portal import (
    # Domain models
    APIKey,
    APIKeyStatus,
    CodeExample,
    SDKLanguage,
    SDKPackage,
    SupportTicket,
    TicketPriority,
    TicketStatus,
    # Application services (for advanced usage)
    APIKeyManager,
    TicketManager,
    SDKGenerator,
    CodeExampleManager,
    # Infrastructure (for testing/mocking)
    InMemoryAPIKeyRepository,
    InMemoryTicketRepository,
    InMemorySDKRepository,
    InMemoryCodeExampleRepository,
    # Main facade (most common usage)
    DeveloperPortalService,
    get_developer_portal_service,
)

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
    # Service facade
    "DeveloperPortalService",
    "get_developer_portal_service",
]
