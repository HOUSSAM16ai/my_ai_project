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
from typing import Any, Optional

logger = logging.getLogger(__name__)


class ServiceLocator:
    """
    Service locator for accessing application services.
    
    This class provides lazy-loaded access to services, reducing
    coupling and circular import issues.
    """
    
    _services_cache = {}
    
    @classmethod
    def get_service(cls, service_name: str) -> Optional[Any]:
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
            if service_name == "master_agent_service":
                from app.services import master_agent_service as svc
            elif service_name == "generation_service":
                from app.services import generation_service as svc
            elif service_name == "admin_ai_service":
                from app.services.admin_ai_service import get_admin_ai_service
                svc = get_admin_ai_service()
            elif service_name == "database_service":
                from app.services import database_service as svc
            elif service_name == "api_gateway_service":
                from app.services.api_gateway_service import get_gateway_service
                svc = get_gateway_service()
            elif service_name == "api_security_service":
                from app.services.api_security_service import get_security_service
                svc = get_security_service()
            elif service_name == "api_observability_service":
                from app.services.api_observability_service import get_observability_service
                svc = get_observability_service()
            elif service_name == "api_contract_service":
                from app.services.api_contract_service import get_contract_service
                svc = get_contract_service()
            elif service_name == "api_governance_service":
                from app.services.api_governance_service import get_governance_service
                svc = get_governance_service()
            elif service_name == "api_slo_sli_service":
                from app.services.api_slo_sli_service import get_slo_service
                svc = get_slo_service()
            elif service_name == "api_config_secrets_service":
                from app.services.api_config_secrets_service import get_config_secrets_service
                svc = get_config_secrets_service()
            elif service_name == "api_disaster_recovery_service":
                from app.services.api_disaster_recovery_service import get_disaster_recovery_service
                svc = get_disaster_recovery_service()
            elif service_name == "api_gateway_chaos":
                from app.services.api_gateway_chaos import get_chaos_service
                svc = get_chaos_service()
            elif service_name == "api_gateway_deployment":
                from app.services.api_gateway_deployment import get_deployment_service
                svc = get_deployment_service()
            else:
                logger.warning(f"Unknown service: {service_name}")
                return None
            
            cls._services_cache[service_name] = svc
            return svc
            
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


def get_admin_ai():
    """Get the admin AI service."""
    return ServiceLocator.get_service("admin_ai_service")


def get_database_service():
    """Get the database service."""
    return ServiceLocator.get_service("database_service")
