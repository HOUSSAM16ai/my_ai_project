"""Repository interface for data access abstraction."""

from abc import ABC, abstractmethod
from typing import Any, TypeVar

T = TypeVar("T")


class RepositoryInterface[T](ABC):
    """Abstract repository interface for data access."""

    @abstractmethod
    def save(self, entity: T) -> T:  # noqa: unused variable
        """Save an entity.

        Args:
            entity: Entity to save

        Returns:
            Saved entity with updated fields
        """

    @abstractmethod
    def find_by_id(self, entity_id: str) -> T | None:
        """Find entity by ID.

        Args:
            entity_id: Entity identifier

        Returns:
            Entity if found, None otherwise
        """

    @abstractmethod
    def find_all(self, filters: dict[str, Any] | None = None) -> list[T]:
        """Find all entities matching filters.

        Args:
            filters: Optional filters to apply

        Returns:
            List of matching entities
        """

    @abstractmethod
    def delete(self, entity_id: str) -> bool:
        """Delete entity by ID.

        Args:
            entity_id: Entity identifier

        Returns:
            True if deleted, False otherwise
        """

    @abstractmethod
    def update(self, entity_id: str, updates: dict[str, Any]) -> T | None:
        """Update entity fields.

        Args:
            entity_id: Entity identifier
            updates: Fields to update

        Returns:
            Updated entity if found, None otherwise
        """
