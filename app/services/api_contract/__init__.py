"""API Contract Service - Hexagonal Architecture.

This package provides API contract management with:
- OpenAPI 3.0 specification support
- Contract validation
- Version management
- Breaking change detection
"""

from .facade import APIContractServiceFacade, get_api_contract_service

__all__ = ["APIContractServiceFacade", "get_api_contract_service"]
