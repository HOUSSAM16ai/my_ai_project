# app/overmind/planning/generators/context_enricher.py
"""
Context enricher with CC ≤ 3.

Enriches context with additional information from various sources.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class EnrichedContext:
    """Enriched context with additional metadata."""
    original: dict[str, Any]
    project_info: dict[str, Any] = field(default_factory=dict)
    environment: dict[str, Any] = field(default_factory=dict)
    constraints: dict[str, Any] = field(default_factory=dict)
    preferences: dict[str, Any] = field(default_factory=dict)


class ContextEnricher:
    """
    Enriches context with additional information.
    
    Complexity: CC=3
    """
    
    def enrich(self, context: dict[str, Any]) -> EnrichedContext:
        """
        Enrich context with additional metadata.
        
        Complexity: CC=3
        """
        project_info = self._extract_project_info(context)
        environment = self._extract_environment(context)
        constraints = self._extract_constraints(context)
        preferences = self._extract_preferences(context)
        
        return EnrichedContext(
            original=context,
            project_info=project_info,
            environment=environment,
            constraints=constraints,
            preferences=preferences,
        )
    
    def _extract_project_info(self, context: dict) -> dict[str, Any]:
        """
        Extract project information from context.
        
        Complexity: CC=2
        """
        return {
            "name": context.get("project_name", "unknown"),
            "language": context.get("language", "python"),
            "framework": context.get("framework"),
            "version": context.get("version"),
        }
    
    def _extract_environment(self, context: dict) -> dict[str, Any]:
        """
        Extract environment information.
        
        Complexity: CC=2
        """
        return {
            "platform": context.get("platform", "linux"),
            "python_version": context.get("python_version", "3.11"),
            "dependencies": context.get("dependencies", []),
        }
    
    def _extract_constraints(self, context: dict) -> dict[str, Any]:
        """
        Extract constraints from context.
        
        Complexity: CC=2
        """
        return {
            "max_tasks": context.get("max_tasks", 50),
            "max_depth": context.get("max_depth", 10),
            "timeout": context.get("timeout", 300),
        }
    
    def _extract_preferences(self, context: dict) -> dict[str, Any]:
        """
        Extract user preferences.
        
        Complexity: CC=2
        """
        return {
            "style": context.get("code_style", "pep8"),
            "testing": context.get("testing_framework", "pytest"),
            "documentation": context.get("documentation_style", "google"),
        }
