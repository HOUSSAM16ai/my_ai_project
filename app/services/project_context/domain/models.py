# app/services/project_context/domain/models.py
"""
Project Context Domain Models
=============================
Pure business logic - no external dependencies
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProjectHealth:
    """Real-time project health metrics."""

    total_files: int = 0
    python_files: int = 0
    test_files: int = 0
    total_lines: int = 0
    models_count: int = 0
    services_count: int = 0
    routes_count: int = 0
    last_updated: str = ""
    issues_found: list[str] = field(default_factory=list)
    strengths: list[str] = field(default_factory=list)


@dataclass
class CodeStatistics:
    """Code statistics for the project."""

    python_files: int = 0
    test_files: int = 0
    total_lines: int = 0
    app_lines: int = 0
    test_lines: int = 0


@dataclass
class ProjectStructure:
    """Project directory structure."""

    directories: list[dict[str, Any]] = field(default_factory=list)
    key_files: list[str] = field(default_factory=list)
    app_modules: list[str] = field(default_factory=list)


@dataclass
class FileAnalysis:
    """Deep file analysis results."""

    total_classes: int = 0
    total_functions: int = 0
    total_imports: int = 0
    key_patterns: list[str] = field(default_factory=list)
    frameworks_detected: list[str] = field(default_factory=list)
    design_patterns: list[str] = field(default_factory=list)


@dataclass
class KeyComponent:
    """Key component information."""

    name: str
    path: str
    description: str
    lines: int


__all__ = [
    "CodeStatistics",
    "FileAnalysis",
    "KeyComponent",
    "ProjectHealth",
    "ProjectStructure",
]
