# app/services/api_security_service.py
"""
API Security Service Adapter
============================
Adapter for the Security System.
"""

from app.services.ai_security import SecurityManager, get_security_manager

# Global singleton instance
security_service = get_security_manager()

def get_security_service() -> SecurityManager:
    """Get the security service instance."""
    return security_service

__all__ = ["SecurityManager", "get_security_service", "security_service"]
