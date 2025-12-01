# app/core/protocols.py
"""
Service Layer Protocols - Enterprise-Grade Interfaces for DI and Testing

This module defines the abstract interfaces (Protocols) for all core
services and gateways in the application. By programming to these interfaces
rather than concrete implementations, we achieve a highly decoupled,
testable, and maintainable architecture.

These protocols are essential for:
-   **Dependency Injection:** Type hinting dependencies with protocols.
-   **Mocking in Tests:** Creating mock objects that conform to these interfaces.
-   **Enforcing Boundaries:** Clearly defining the public API of each service.
"""

from __future__ import annotations

from typing import Any, Protocol


class DatabaseProtocol(Protocol):
    """Interface for database operations."""

    def get_record(self, table_name: str, record_id: int) -> dict[str, Any]: ...

    def get_all_records(self, table_name: str) -> list[dict[str, Any]]: ...

    def create_record(self, table_name: str, data: dict[str, Any]) -> dict[str, Any]: ...

    def update_record(
        self, table_name: str, record_id: int, data: dict[str, Any]
    ) -> dict[str, Any]: ...

    def delete_record(self, table_name: str, record_id: int) -> dict[str, Any]: ...

    def execute_query(self, sql: str) -> dict[str, Any]: ...


class UserRepositoryProtocol(Protocol):
    """Interface for user management operations."""

    def get_all_users(self) -> list[Any]: ...

    def create_new_user(
        self, full_name: str, email: str, password: str, is_admin: bool
    ) -> dict[str, str]: ...

    def ensure_admin_user_exists(self) -> dict[str, str]: ...

    def get_user_by_email(self, email: str) -> Any | None: ...


class AIClientProtocol(Protocol):
    """Interface for interacting with an AI model or service."""

    def stream_chat(
        self, question: str, conversation_id: str | None, user_id: int | str
    ) -> Any: ...


class MessageQueueProtocol(Protocol):
    """Interface for a message broker (e.g., RabbitMQ, Kafka)."""

    def publish(self, topic: str, message: dict[str, Any]) -> None: ...

    def subscribe(self, topic: str, callback: Any) -> None: ...


class CacheProtocol(Protocol):
    """Interface for a caching service (e.g., Redis, Memcached)."""

    def get(self, key: str) -> Any | None: ...

    def set(self, key: str, value: Any, ttl: int) -> None: ...

    def delete(self, key: str) -> None: ...


class NotificationProtocol(Protocol):
    """Interface for sending notifications (e.g., email, SMS)."""

    def send(self, recipient: str, message: str, subject: str | None = None) -> None: ...


class VectorStoreProtocol(Protocol):
    """Interface for a vector database (e.g., Pinecone, Weaviate)."""

    def upsert(self, vectors: list[dict[str, Any]], namespace: str) -> None: ...

    def query(self, vector: list[float], top_k: int, namespace: str) -> list[dict[str, Any]]: ...
