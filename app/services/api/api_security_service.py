# app/services/api_security_service.py
"""
API Security Service Adapter
============================
Adapter for the Superhuman Security System.
"""

from app.services.ai_engineering.ai_advanced_security import SuperhumanSecuritySystem

# Global singleton instance
security_service = SuperhumanSecuritySystem()


def get_security_service() -> SuperhumanSecuritySystem:
    """Get the security service instance."""
    return security_service


__all__ = ["SuperhumanSecuritySystem", "get_security_service", "security_service"]
