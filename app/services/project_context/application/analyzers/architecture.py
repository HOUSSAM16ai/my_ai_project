"""
Architecture Analyzer
=====================
Detects architectural layers.
"""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class ArchitectureAnalyzer:
    """Analyzer for architecture layers."""

    project_root: Path

    def analyze(self) -> dict[str, list[str]]:
        """Identify architecture layers."""
        layers = {
            "presentation": [],
            "business": [],
            "data": [],
            "infrastructure": [],
            "core": [],
        }

        app_dir = self.project_root / "app"
        if not app_dir.exists():
            return layers

        dir_mapping = {
            "api": "presentation",
            "routers": "presentation",
            "templates": "presentation",
            "static": "presentation",
            "services": "business",
            "overmind": "business",
            "models": "data",
            "core": "core",
            "utils": "core",
            "middleware": "infrastructure",
            "config": "infrastructure",
        }

        for item in app_dir.iterdir():
            if item.is_dir() and not item.name.startswith("__"):
                layer = dir_mapping.get(item.name, "business")
                py_count = len(list(item.glob("*.py")))
                if py_count > 0:
                    layers[layer].append(f"{item.name}/ ({py_count} files)")

        return layers
