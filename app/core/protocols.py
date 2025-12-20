"""
Core Protocols & Interfaces
Defines abstract base classes and protocols for the application.
"""
from typing import Any, Protocol, runtime_checkable

# We define the interface here directly or import from a valid location
# To fix the "ModuleNotFoundError: No module named 'app.core.interfaces'", we remove the bad import.

@runtime_checkable
class BaseService(Protocol):
    """Base protocol for all application services."""
    pass

@runtime_checkable
class RepositoryProtocol(Protocol):
    """Base protocol for repositories."""
    pass
