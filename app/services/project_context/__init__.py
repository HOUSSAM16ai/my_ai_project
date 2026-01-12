# app/services/project_context/__init__.py
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


# Define helper functions that were expected by the legacy shim
def get_project_context_service() -> ProjectContextService:
    """Factory to get the singleton instance of ProjectContextService."""
    return ProjectContextService()


async def get_project_context_for_ai() -> dict:
    """Convenience function to get AI-ready context summary."""
    service = get_project_context_service()
    return await service.get_ai_context_summary()


__all__ = [
    "CodeStatistics",
    "FileAnalysis",
    "KeyComponent",
    # Application service
    "ProjectContextService",
    # Domain models
    "ProjectHealth",
    "ProjectStructure",
    "get_project_context_for_ai",
    # Helper functions
    "get_project_context_service",
]
