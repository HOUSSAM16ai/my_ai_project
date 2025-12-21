"""
Service Locator - Centralized Service Access
============================================

This module provides a service locator pattern to reduce coupling between
components and services. Instead of importing services directly throughout
the codebase, use this locator to access services dynamically.

Benefits:
- Reduces import coupling
- Lazy loading of services
- Easier testing (can mock services)
- Single point of service access
"""

import logging
from typing import Any, ClassVar

logger = logging.getLogger(__name__)


class ServiceLocator:
    """
    Service locator for accessing application services.

    This class provides lazy-loaded access to services, reducing
    coupling and circular import issues.
    """

    _services_cache: ClassVar[dict[str, Any]] = {}

    @classmethod
    def get_service(cls, service_name: str) -> Any | None:
        """
        Get a service by name.

        Args:
            service_name: Name of the service module (e.g., 'master_agent_service')

        Returns:
            Service module or None if not available
        """
        if service_name in cls._services_cache:
            return cls._services_cache[service_name]

        try:
            # Lazy import to avoid circular dependencies
            # Only active services after simplification
            if service_name == "master_agent_service":
                from app.services import master_agent_service as service_module
            elif service_name == "generation_service":
                from app.services import generation_service as service_module
            elif service_name == "database_service":
                from app.services.system.database_service import database_service as service_module
            elif service_name == "api_security_service":
                from app.services.api.api_security_service import security_service as service_module
            elif service_name == "api_governance_service":
                from app.services.api.api_governance_service import governance_service as service_module
            elif service_name == "api_config_secrets_service":
                from app.services.api.api_config_secrets_service import (
                    config_secrets_service as service_module,
                )
            elif service_name == "admin_ai_service":
                from app.services import admin_ai_service as service_module
            else:
                logger.warning(f"Unknown service: {service_name}")
                return None

            cls._services_cache[service_name] = service_module
            return service_module

        except ImportError as e:
            logger.debug(f"Service '{service_name}' not available: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading service '{service_name}': {e}")
            return None

    @classmethod
    def clear_cache(cls):
        """Clear the service cache. Useful for testing."""
        cls._services_cache.clear()

    @classmethod
    def is_available(cls, service_name: str) -> bool:
        """
        Check if a service is available.

        Args:
            service_name: Name of the service

        Returns:
            True if service is available, False otherwise
        """
        return cls.get_service(service_name) is not None


# Convenience functions for commonly used services
def get_overmind():
    """Get the master agent (overmind) service."""
    return ServiceLocator.get_service("master_agent_service")


def get_maestro():
    """Get the generation (maestro) service."""
    return ServiceLocator.get_service("generation_service")


def get_database_service():
    """Get the database service."""
    return ServiceLocator.get_service("database_service")

def get_admin_ai():
    """Get the admin AI service."""
    return ServiceLocator.get_service("admin_ai_service")
