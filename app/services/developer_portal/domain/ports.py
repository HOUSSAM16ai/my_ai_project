# app/services/developer_portal/domain/ports.py
"""
Developer Portal Domain Ports
==============================
Interface definitions for repositories and external services.
"""

from abc import ABC, abstractmethod
from typing import Protocol

from app.services.developer_portal.domain.models import (
    APIKey,
    CodeExample,
    SDKPackage,
    SupportTicket,
)


class APIKeyRepository(Protocol):
    """Repository for API key management"""

    def create(self, api_key: APIKey) -> str:
        """Create new API key"""
        ...

    def get(self, key_id: str) -> APIKey | None:
        """Get API key by ID"""
        ...

    def update(self, api_key: APIKey) -> None:
        """Update API key"""
        ...

    def delete(self, key_id: str) -> None:
        """Delete API key"""
        ...

    def list_by_developer(self, developer_id: str) -> list[APIKey]:
        """List all keys for a developer"""
        ...


class TicketRepository(Protocol):
    """Repository for support ticket management"""

    def create(self, ticket: SupportTicket) -> str:
        """Create new support ticket"""
        ...

    def get(self, ticket_id: str) -> SupportTicket | None:
        """Get ticket by ID"""
        ...

    def update(self, ticket: SupportTicket) -> None:
        """Update ticket"""
        ...

    def list_by_developer(self, developer_id: str) -> list[SupportTicket]:
        """List tickets for a developer"""
        ...


class SDKRepository(Protocol):
    """Repository for SDK package management"""

    def create(self, sdk: SDKPackage) -> str:
        """Create new SDK package record"""
        ...

    def get(self, sdk_id: str) -> SDKPackage | None:
        """Get SDK by ID"""
        ...

    def list_by_language(self, language: str) -> list[SDKPackage]:
        """List SDKs for a language"""
        ...


class CodeExampleRepository(Protocol):
    """Repository for code examples"""

    def create(self, example: CodeExample) -> str:
        """Create new code example"""
        ...

    def get(self, example_id: str) -> CodeExample | None:
        """Get example by ID"""
        ...

    def list_by_category(self, category: str) -> list[CodeExample]:
        """List examples by category"""
        ...


__all__ = [
    "APIKeyRepository",
    "TicketRepository",
    "SDKRepository",
    "CodeExampleRepository",
]
