"""
Component Analyzer
==================
Identifies key components in the system.
"""

from dataclasses import dataclass
from pathlib import Path

from app.services.project_context.domain.models import KeyComponent

@dataclass
class ComponentAnalyzer:
    """Analyzer for identifying key components."""

    project_root: Path

    def analyze(self) -> list[KeyComponent]:
        """Identify key components."""
        components: list[KeyComponent] = []

        key_files = [
            ("app/main.py", "Application Entry Point", "FastAPI app creation"),
            ("app/core/database.py", "Database Engine", "Async database connections"),
            ("app/core/ai_gateway.py", "AI Gateway", "Neural routing mesh for AI"),
            ("app/core/prompts.py", "System Prompts", "OVERMIND identity and context"),
            ("app/services/overmind/orchestrator.py", "Overmind Orchestrator", "Mission orchestration"),
            ("app/services/agent_tools/__init__.py", "Agent Tools", "File ops, search, reasoning"),
            ("app/api/routers/admin.py", "Admin API", "Chat and admin endpoints"),
        ]

        for file_path, name, description in key_files:
            full_path = self.project_root / file_path
            if full_path.exists():
                try:
                    lines = len(full_path.read_text(encoding="utf-8").splitlines())
                    components.append(
                        KeyComponent(
                            name=name,
                            path=file_path,
                            description=description,
                            lines=lines,
                        )
                    )
                except Exception:
                    pass

        return components
