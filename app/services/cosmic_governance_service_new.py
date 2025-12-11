# app/services/cosmic_governance_service.py
"""
Cosmic Governance Service - LEGACY COMPATIBILITY
=================================================
This file now imports from the refactored governance module.

Original file: 714+ lines
Refactored: Delegates to governance/ module following Hexagonal Architecture

For new code, import from: app.services.governance
"""

# Legacy imports for backward compatibility
from app.services.governance import CosmicGovernanceService

# Re-export for backward compatibility
__all__ = [
    "CosmicGovernanceService",
]
