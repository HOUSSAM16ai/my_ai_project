# app/services/api_governance_service.py
"""
API Governance Service Adapter
==============================
Adapter for the Cosmic Governance Service.
"""

from app.services.governance import CosmicGovernanceService

# Global singleton instance
governance_service = CosmicGovernanceService()

def get_governance_service() -> CosmicGovernanceService:
    """Get the governance service instance."""
    return governance_service

__all__ = ["CosmicGovernanceService", "get_governance_service", "governance_service"]
