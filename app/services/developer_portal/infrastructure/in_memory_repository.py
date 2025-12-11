# app/services/developer_portal/infrastructure/in_memory_repository.py
"""In-Memory Repository Implementations"""

from app.services.developer_portal.domain.models import (
    APIKey,
    SupportTicket,
    SDKPackage,
    CodeExample,
)


class InMemoryAPIKeyRepository:
    """In-memory storage for API keys"""

    def __init__(self):
        self._keys: dict[str, APIKey] = {}

    def create(self, api_key: APIKey) -> str:
        self._keys[api_key.key_id] = api_key
        return api_key.key_id

    def get(self, key_id: str) -> APIKey | None:
        return self._keys.get(key_id)

    def update(self, api_key: APIKey) -> None:
        self._keys[api_key.key_id] = api_key

    def delete(self, key_id: str) -> None:
        self._keys.pop(key_id, None)

    def list_by_developer(self, developer_id: str) -> list[APIKey]:
        return [k for k in self._keys.values() if k.developer_id == developer_id]


class InMemoryTicketRepository:
    """In-memory storage for support tickets"""

    def __init__(self):
        self._tickets: dict[str, SupportTicket] = {}

    def create(self, ticket: SupportTicket) -> str:
        self._tickets[ticket.ticket_id] = ticket
        return ticket.ticket_id

    def get(self, ticket_id: str) -> SupportTicket | None:
        return self._tickets.get(ticket_id)

    def update(self, ticket: SupportTicket) -> None:
        self._tickets[ticket.ticket_id] = ticket

    def list_by_developer(self, developer_id: str) -> list[SupportTicket]:
        return [t for t in self._tickets.values() if t.developer_id == developer_id]


class InMemorySDKRepository:
    """In-memory storage for SDK packages"""

    def __init__(self):
        self._sdks: dict[str, SDKPackage] = {}

    def create(self, sdk: SDKPackage) -> str:
        self._sdks[sdk.sdk_id] = sdk
        return sdk.sdk_id

    def get(self, sdk_id: str) -> SDKPackage | None:
        return self._sdks.get(sdk_id)

    def list_by_language(self, language: str) -> list[SDKPackage]:
        return [s for s in self._sdks.values() if s.language.value == language]


class InMemoryCodeExampleRepository:
    """In-memory storage for code examples"""

    def __init__(self):
        self._examples: dict[str, CodeExample] = {}

    def create(self, example: CodeExample) -> str:
        self._examples[example.example_id] = example
        return example.example_id

    def get(self, example_id: str) -> CodeExample | None:
        return self._examples.get(example_id)

    def list_by_category(self, category: str) -> list[CodeExample]:
        return [e for e in self._examples.values() if e.category == category]
