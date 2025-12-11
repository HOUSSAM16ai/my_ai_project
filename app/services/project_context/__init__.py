# app/services/project_context/__init__.py
"""
Project Context Service
=======================
Refactored using Hexagonal Architecture for maximum maintainability

Import everything from this module for backward compatibility
"""

# Domain models
from .domain.models import (
    CodeStatistics,
    FileAnalysis,
    KeyComponent,
    ProjectHealth,
    ProjectStructure,
)

# Application service
from .application.context_analyzer import ProjectContextService

# Facade (backward compatible)
from .facade import get_project_context_for_ai, get_project_context_service

__all__ = [
    # Domain models
    "ProjectHealth",
    "CodeStatistics",
    "ProjectStructure",
    "FileAnalysis",
    "KeyComponent",
    # Application service
    "ProjectContextService",
    # Facade functions
    "get_project_context_service",
    "get_project_context_for_ai",
]
