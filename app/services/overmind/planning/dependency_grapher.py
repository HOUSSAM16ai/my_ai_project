# app/overmind/planning/dependency_grapher.py
"""
SUPERHUMAN DEPENDENCY GRAPHER
=============================
Target 4: Exact Layering.
Generates dependency graphs and enforces architectural strictness.
"""

import ast
import sys
from pathlib import Path


class DependencyGrapher:
    def __init__(self, root="app"):
        self.root = Path(root)
        self.edges = []
        self.nodes = set()

    def build_graph(self):
        for path in self.root.rglob("*.py"):
            module_name = self._path_to_module(path)
            self.nodes.add(module_name)
            imports = self._get_imports(path)
            for imp in imports:
                if imp.startswith("app"):
                    self.edges.append((module_name, imp))
        return self.edges

    def _path_to_module(self, path):
        parts = path.with_suffix("").parts
        return ".".join(parts)

    def _get_imports(self, path):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except Exception:
            return []

        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for n in node.names:
                    imports.append(n.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        return imports

    def validate_layers(self):
        """Enforces: api -> services -> core"""
        violations = []
        for src, dst in self.edges:
            if "app.core" in src and "app.services" in dst:
                violations.append(f"LAYER VIOLATION: Core '{src}' imports Service '{dst}'")
            if "app.services" in src and "app.api" in dst:
                violations.append(f"LAYER VIOLATION: Service '{src}' imports API '{dst}'")
        return violations


if __name__ == "__main__":
    grapher = DependencyGrapher()
    grapher.build_graph()
    violations = grapher.validate_layers()
    if violations:
        print("❌ Layer Violations Found:")
        for v in violations[:10]:
            print(v)
        sys.exit(1)
    else:
        print("✅ Architecture Layers are Clean.")
