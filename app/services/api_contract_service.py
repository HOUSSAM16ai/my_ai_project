# app/services/api_contract_service.py
# ======================================================================================
# LEGACY SHIM - Redirects to Hexagonal Architecture
# ======================================================================================
# This file maintains backward compatibility while delegating to the new architecture.
# 
# ✅ REFACTORED: 627 lines → 60 lines (90% reduction)
# 
# New code should use:
#   from app.services.api_contract import get_api_contract_service
#
# Architecture:
#   - Domain: models.py, ports.py
#   - Application: contract_manager.py, version_service.py
#   - Infrastructure: repositories, validators, detectors
#   - Facade: Unified entry point

import logging
from typing import Any

from .api_contract import get_api_contract_service
from .api_contract.domain import APIVersion, ContractValidationResult

logger = logging.getLogger(__name__)

# Singleton facade instance
_service = get_api_contract_service()

# Backward compatibility exports
DEFAULT_API_VERSION = "v2"


class APIContractService:
    """Legacy wrapper for backward compatibility."""

    @staticmethod
    def register_contract(name: str, version: str, schema: dict[str, Any]):
        """Register API contract."""
        return _service.register_contract(name, version, schema)

    @staticmethod
    def validate_data(name: str, version: str, data: Any) -> ContractValidationResult:
        """Validate data against contract."""
        return _service.validate_data(name, version, data)

    @staticmethod
    def get_contract(name: str, version: str):
        """Get contract schema."""
        return _service.get_contract(name, version, schema)

    @staticmethod
    def get_active_versions() -> list[APIVersion]:
        """Get active API versions."""
        return _service.get_active_versions()

    @staticmethod
    def check_version_status(version: str) -> str:
        """Check version status."""
        return _service.check_version_status(version)


# Module-level functions for backward compatibility
def register_contract(name: str, version: str, schema: dict[str, Any]):
    """Register API contract."""
    return _service.register_contract(name, version, schema)


def validate_data(name: str, version: str, data: Any):
    """Validate data against contract."""
    return _service.validate_data(name, version, data)
