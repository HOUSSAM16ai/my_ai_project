# app/services/project_context/facade.py
"""
Project Context Service Facade
==============================
Backward-compatible facade providing unified access to project context analysis
"""

from __future__ import annotations

from pathlib import Path

from .application.context_analyzer import ProjectContextService

# ======================================================================================
# SINGLETON INSTANCES
# ======================================================================================

_project_context_service: ProjectContextService | None = None


def get_project_context_service(project_root: Path | None = None) -> ProjectContextService:
    """Get the singleton ProjectContextService instance."""
    global _project_context_service
    if _project_context_service is None:
        _project_context_service = ProjectContextService(project_root=project_root)
    return _project_context_service


def get_project_context_for_ai() -> str:
    """Convenience function to get AI context."""
    return get_project_context_service().generate_context_for_ai()


__all__ = [
    "ProjectContextService",
    "get_project_context_service",
    "get_project_context_for_ai",
]
