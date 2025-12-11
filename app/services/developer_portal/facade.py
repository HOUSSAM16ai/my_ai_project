# app/services/developer_portal/facade.py
"""
Developer Portal Service Facade
===============================
Backward-compatible facade maintaining original API.
"""

import threading
from typing import Any

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
from app.services.developer_portal.application.api_key_manager import APIKeyManager
from app.services.developer_portal.application.ticket_manager import TicketManager
from app.services.developer_portal.application.sdk_generator import SDKGenerator
from app.services.developer_portal.application.code_example_manager import (
    CodeExampleManager,
)
from app.services.developer_portal.infrastructure.in_memory_repository import (
    InMemoryAPIKeyRepository,
    InMemoryTicketRepository,
    InMemorySDKRepository,
    InMemoryCodeExampleRepository,
)


class DeveloperPortalService:
    """
    Developer Portal Service Facade.
    
    Maintains backward compatibility with original monolithic API
    while delegating to clean hexagonal architecture.
    """

    def __init__(self):
        # Infrastructure
        self._key_repo = InMemoryAPIKeyRepository()
        self._ticket_repo = InMemoryTicketRepository()
        self._sdk_repo = InMemorySDKRepository()
        self._example_repo = InMemoryCodeExampleRepository()

        # Application services
        self._key_manager = APIKeyManager(self._key_repo)
        self._ticket_manager = TicketManager(self._ticket_repo)
        self._sdk_generator = SDKGenerator(self._sdk_repo)
        self._example_manager = CodeExampleManager(self._example_repo)

    # API Key Management
    def generate_api_key(
        self,
        developer_id: str,
        name: str,
        scopes: list[str],
        expires_in_days: int | None = None,
    ) -> APIKey:
        """Generate new API key"""
        return self._key_manager.generate_key(developer_id, name, scopes, expires_in_days)

    def validate_api_key(self, key_value: str) -> APIKey | None:
        """Validate API key"""
        return self._key_manager.validate_key(key_value)

    def revoke_api_key(self, key_id: str, reason: str) -> bool:
        """Revoke API key"""
        return self._key_manager.revoke_key(key_id, reason)

    def rotate_api_key(self, key_id: str) -> APIKey | None:
        """Rotate API key"""
        return self._key_manager.rotate_key(key_id)

    def list_developer_keys(self, developer_id: str) -> list[APIKey]:
        """List all keys for developer"""
        return self._key_repo.list_by_developer(developer_id)

    # Support Tickets
    def create_support_ticket(
        self,
        developer_id: str,
        subject: str,
        description: str,
        priority: TicketPriority = TicketPriority.MEDIUM,
        category: str = "general",
    ) -> SupportTicket:
        """Create support ticket"""
        return self._ticket_manager.create_ticket(
            developer_id, subject, description, priority, category
        )

    def assign_ticket(self, ticket_id: str, assignee: str) -> bool:
        """Assign ticket to agent"""
        return self._ticket_manager.assign_ticket(ticket_id, assignee)

    def resolve_ticket(self, ticket_id: str) -> bool:
        """Resolve ticket"""
        return self._ticket_manager.resolve_ticket(ticket_id)

    def close_ticket(self, ticket_id: str) -> bool:
        """Close ticket"""
        return self._ticket_manager.close_ticket(ticket_id)

    def add_ticket_message(self, ticket_id: str, sender: str, message: str) -> bool:
        """Add message to ticket"""
        return self._ticket_manager.add_message(ticket_id, sender, message)

    def list_developer_tickets(self, developer_id: str) -> list[SupportTicket]:
        """List developer tickets"""
        return self._ticket_repo.list_by_developer(developer_id)

    # SDK Generation
    def generate_sdk(self, language: SDKLanguage, api_version: str) -> SDKPackage:
        """Generate SDK package"""
        return self._sdk_generator.generate_sdk(language, api_version)

    def list_sdks_by_language(self, language: SDKLanguage) -> list[SDKPackage]:
        """List SDKs for language"""
        return self._sdk_repo.list_by_language(language.value)

    # Code Examples
    def create_code_example(
        self,
        title: str,
        description: str,
        language: SDKLanguage,
        code: str,
        endpoint: str,
        category: str = "general",
        tags: list[str] | None = None,
    ) -> CodeExample:
        """Create code example"""
        return self._example_manager.create_example(
            title, description, language, code, endpoint, category, tags
        )

    def get_examples_by_category(self, category: str) -> list[CodeExample]:
        """Get examples by category"""
        return self._example_manager.get_examples_by_category(category)


# Singleton instance
_service_instance: DeveloperPortalService | None = None
_service_lock = threading.Lock()


def get_developer_portal_service() -> DeveloperPortalService:
    """Get singleton instance"""
    global _service_instance

    if _service_instance is None:
        with _service_lock:
            if _service_instance is None:
                _service_instance = DeveloperPortalService()

    return _service_instance
