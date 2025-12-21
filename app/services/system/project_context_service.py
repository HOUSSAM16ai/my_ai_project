# app/services/project_context_service.py
"""
🧠 PROJECT CONTEXT SERVICE - LEGACY COMPATIBILITY SHIM
======================================================

Overmind Intelligence Layer - Project Understanding Service
This file maintains backward compatibility by delegating to the refactored
hexagonal architecture in app/services/project_context/

Original file: 685 lines
Refactored: Delegates to project_context/ module

SOLID PRINCIPLES APPLIED:
  - Single Responsibility: Each component has one clear purpose
  - Open/Closed: Open for extension, closed for modification
  - Liskov Substitution: All implementations are interchangeable
  - Interface Segregation: Small focused interfaces
  - Dependency Inversion: Depends on abstractions

For new code, import from: app.services.project_context
This shim exists for backward compatibility only.
"""

from __future__ import annotations

# Re-export everything from the refactored hexagonal architecture
from app.services.project_context import (
    # Domain models
    CodeStatistics,
    FileAnalysis,
    KeyComponent,
    # Application service
    ProjectContextService,
    ProjectHealth,
    ProjectStructure,
    # Facade functions (most common usage)
    get_project_context_for_ai,
    get_project_context_service,
)

__all__ = [
    # Models
    "ProjectHealth",
    "CodeStatistics",
    "ProjectStructure",
    "FileAnalysis",
    "KeyComponent",
    # Service
    "ProjectContextService",
    # Convenience functions
    "get_project_context_service",
    "get_project_context_for_ai",
]
