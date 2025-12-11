# app/services/governance/__init__.py
"""
Governance Module - Cosmic Governance
======================================
Cosmic governance service following Hexagonal Architecture.

Refactored from monolithic CosmicGovernanceService (714 lines)
into clean layered architecture.

Architecture:
- Domain Layer: Pure business logic and entities
- Application Layer: Use cases and orchestration
- Infrastructure Layer: External adapters and persistence
- Facade: Backward-compatible API
"""

from app.services.governance.facade import CosmicGovernanceService

__all__ = [
    "CosmicGovernanceService",
]
