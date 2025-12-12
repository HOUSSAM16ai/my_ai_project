"""Domain ports (interfaces) for API Contract service."""

from abc import ABC, abstractmethod
from typing import Any

from .models import (
    APIVersion,
    BreakingChange,
    ContractSchema,
    ContractValidationResult,
)


class ContractRepository(ABC):
    """Repository for contract storage."""

    @abstractmethod
    def save_contract(self, contract: ContractSchema) -> None:
        """Save a contract schema."""
        pass

    @abstractmethod
    def get_contract(self, name: str, version: str) -> ContractSchema | None:
        """Retrieve a contract schema."""
        pass

    @abstractmethod
    def list_contracts(self) -> list[ContractSchema]:
        """List all contracts."""
        pass


class SchemaValidator(ABC):
    """Schema validation interface."""

    @abstractmethod
    def validate(self, data: Any, schema: dict[str, Any]) -> ContractValidationResult:
        """Validate data against schema."""
        pass


class BreakingChangeDetector(ABC):
    """Breaking change detection interface."""

    @abstractmethod
    def detect_changes(
        self, old_schema: dict[str, Any], new_schema: dict[str, Any]
    ) -> list[BreakingChange]:
        """Detect breaking changes between schemas."""
        pass


class VersionManager(ABC):
    """API version management interface."""

    @abstractmethod
    def get_version(self, version: str) -> APIVersion | None:
        """Get version metadata."""
        pass

    @abstractmethod
    def list_versions(self) -> list[APIVersion]:
        """List all API versions."""
        pass

    @abstractmethod
    def is_version_active(self, version: str) -> bool:
        """Check if version is active."""
        pass
