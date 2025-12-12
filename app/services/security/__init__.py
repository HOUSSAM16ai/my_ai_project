"""
Security Services Module
Extracted from app/api/routers/security.py for Separation of Concerns
"""

from app.services.security.auth_persistence import AuthPersistence

__all__ = ["AuthPersistence"]
