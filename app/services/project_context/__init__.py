"""
Project Context Service
======================

This module provides services for managing project context, including:
- Knowledge graph management
- Codebase indexing and retrieval
- Context summarization
- Dependency analysis

The service is designed with a hexagonal architecture, separating domain logic
from infrastructure concerns.
"""

from app.services.project_context.application.context_analyzer import ProjectContextService
from app.services.project_context.domain.models import (
    CodeStatistics,
    FileAnalysis,
    KeyComponent,
    ProjectHealth,
    ProjectStructure,
)

__all__ = [
    "CodeStatistics",
    "FileAnalysis",
    "KeyComponent",
    # Application service
    "ProjectContextService",
    # Domain models
    "ProjectHealth",
    "ProjectStructure",
]
