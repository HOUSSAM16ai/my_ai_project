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
        """
        تحديد طبقات البنية المعمارية
        Identify architecture layers.
        """
        layers = self._initialize_layers()

        app_dir = self.project_root / "app"
        if not app_dir.exists():
            return layers

        dir_mapping = self._get_directory_layer_mapping()
        self._categorize_directories(app_dir, dir_mapping, layers)

        return layers

    def _initialize_layers(self) -> dict[str, list[str]]:
        """
        تهيئة الطبقات الفارغة
        Initialize empty layer structure.
        """
        return {
            "presentation": [],
            "business": [],
            "data": [],
            "infrastructure": [],
            "core": [],
        }

    def _get_directory_layer_mapping(self) -> dict[str, str]:
        """
        الحصول على تعيين الدليل إلى الطبقة
        Get mapping from directory name to layer.
        """
        return {
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

    def _categorize_directories(
        self,
        app_dir: Path,
        dir_mapping: dict[str, str],
        layers: dict[str, list[str]],
    ) -> None:
        """
        تصنيف الدلائل إلى طبقات
        Categorize directories into layers.
        """
        for item in app_dir.iterdir():
            if item.is_dir() and not item.name.startswith("__"):
                layer = dir_mapping.get(item.name, "business")
                py_count = len(list(item.glob("*.py")))
                if py_count > 0:
                    layers[layer].append(f"{item.name}/ ({py_count} files)")
