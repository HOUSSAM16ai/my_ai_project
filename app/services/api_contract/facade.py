"""Facade for API Contract service - Hexagonal Architecture entry point."""

import logging
from typing import Any

from .application.contract_manager import ContractManager
from .application.version_service import VersionService
from .domain.models import APIVersion, ContractSchema, ContractValidationResult
from .infrastructure.change_detector import SimpleBreakingChangeDetector
from .infrastructure.in_memory_repository import InMemoryContractRepository
from .infrastructure.jsonschema_validator import JSONSchemaValidator
from .infrastructure.version_manager import InMemoryVersionManager

logger = logging.getLogger(__name__)


class APIContractServiceFacade:
    """Unified facade for API Contract service."""

    def __init__(self):
        # Infrastructure layer
        self._repository = InMemoryContractRepository()
        self._validator = JSONSchemaValidator()
        self._change_detector = SimpleBreakingChangeDetector()
        self._version_manager = InMemoryVersionManager()

        # Application layer
        self._contract_manager = ContractManager(
            self._repository, self._validator, self._change_detector
        )
        self._version_service = VersionService(self._version_manager)

        logger.info("APIContractServiceFacade initialized")

    # Contract Management
    def register_contract(
        self, name: str, version: str, schema: dict[str, Any]
    ) -> ContractSchema:
        """Register a new API contract."""
        return self._contract_manager.register_contract(name, version, schema)

    def validate_data(
        self, name: str, version: str, data: Any
    ) -> ContractValidationResult:
        """Validate data against a contract."""
        return self._contract_manager.validate_against_contract(name, version, data)

    def get_contract(self, name: str, version: str) -> ContractSchema | None:
        """Get a specific contract."""
        return self._contract_manager.get_contract(name, version)

    def list_contracts(self) -> list[ContractSchema]:
        """List all contracts."""
        return self._contract_manager.list_all_contracts()

    # Version Management
    def get_active_versions(self) -> list[APIVersion]:
        """Get all active API versions."""
        return self._version_service.get_active_versions()

    def check_version_status(self, version: str) -> str:
        """Check version status."""
        return self._version_service.check_version_status(version)

    def is_version_supported(self, version: str) -> bool:
        """Check if version is supported."""
        return self._version_service.is_version_supported(version)

    def get_version_info(self, version: str) -> APIVersion | None:
        """Get version information."""
        return self._version_service.get_version_info(version)

    def get_breaking_changes(self, version: str) -> list[str]:
        """Get breaking changes for a version."""
        return self._version_service.get_breaking_changes(version)


# Singleton instance
_facade_instance: APIContractServiceFacade | None = None


def get_api_contract_service() -> APIContractServiceFacade:
    """Get or create the singleton facade instance."""
    global _facade_instance
    if _facade_instance is None:
        _facade_instance = APIContractServiceFacade()
    return _facade_instance
