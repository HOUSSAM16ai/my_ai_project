"""Service interface for application services."""

from abc import ABC, abstractmethod
from typing import Any


class ServiceInterface(ABC):
    """Abstract interface for application services."""

    @abstractmethod
    def execute(self, request: dict[str, Any]) -> dict[str, Any]:
        """Execute service operation.

        Args:
            request: Service request data

        Returns:
            Service response data
        """

    @abstractmethod
    def validate_request(self, request: dict[str, Any]) -> bool:
        """Validate service request.

        Args:
            request: Request to validate

        Returns:
            True if valid, False otherwise
        """

    @abstractmethod
    def get_name(self) -> str:
        """Get service name.

        Returns:
            Service name string
        """
