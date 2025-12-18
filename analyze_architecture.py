#!/usr/bin/env python3
"""
Architecture Analyzer
Identifies architectural issues, circular dependencies, and coupling problems.
"""
import ast
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


class DependencyAnalyzer(ast.NodeVisitor):
    """Analyzes module dependencies."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.imports = set()
        self.from_imports = defaultdict(set)

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            for alias in node.names:
                self.from_imports[node.module].add(alias.name)
        self.generic_visit(node)


def analyze_dependencies(root_dir: str = "app") -> dict[str, Any]:
    """Analyze project dependencies and coupling."""
    root_path = Path(root_dir)
    module_deps = {}
    
    for py_file in root_path.rglob("*.py"):
        if "__pycache__" in str(py_file) or "test_" in py_file.name:
            continue

        try:
            with open(py_file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read(), filename=str(py_file))
            
            analyzer = DependencyAnalyzer(str(py_file))
            analyzer.visit(tree)
            
            module_name = str(py_file.relative_to(root_path)).replace("/", ".").replace(".py", "")
            module_deps[module_name] = {
                "imports": list(analyzer.imports),
                "from_imports": {k: list(v) for k, v in analyzer.from_imports.items()},
                "total_deps": len(analyzer.imports) + len(analyzer.from_imports),
            }
        except Exception:
            pass

    # Find highly coupled modules
    highly_coupled = [
        (module, data["total_deps"])
        for module, data in module_deps.items()
        if data["total_deps"] > 15
    ]
    highly_coupled.sort(key=lambda x: x[1], reverse=True)

    # Detect circular dependencies (simplified)
    circular_deps = []
    for module, data in module_deps.items():
        for imported in data["from_imports"].keys():
            if imported.startswith("app.") and imported in module_deps:
                # Check if imported module imports back
                imported_data = module_deps[imported]
                for imp in imported_data["from_imports"].keys():
                    if module.startswith(imp):
                        circular_deps.append((module, imported))

    return {
        "total_modules": len(module_deps),
        "highly_coupled": highly_coupled[:20],
        "circular_dependencies": circular_deps[:10],
        "module_dependencies": module_deps,
    }


def analyze_layer_violations(root_dir: str = "app") -> dict[str, Any]:
    """Detect violations of layered architecture."""
    violations = []
    
    # Define architectural layers
    layers = {
        "presentation": ["api", "blueprints"],
        "application": ["services", "boundaries"],
        "domain": ["domain", "models"],
        "infrastructure": ["infrastructure", "core.database"],
    }
    
    # Layer dependency rules (who can depend on whom)
    allowed_deps = {
        "presentation": ["application", "domain"],
        "application": ["domain", "infrastructure"],
        "domain": [],  # Domain should not depend on other layers
        "infrastructure": ["domain"],
    }
    
    root_path = Path(root_dir)
    for py_file in root_path.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
            
        try:
            with open(py_file, "r", encoding="utf-8") as f:
                tree = ast.parse(f.read())
            
            # Determine file's layer
            file_layer = None
            rel_path = str(py_file.relative_to(root_path))
            for layer, patterns in layers.items():
                if any(pattern in rel_path for pattern in patterns):
                    file_layer = layer
                    break
            
            if not file_layer:
                continue
            
            # Check imports
            analyzer = DependencyAnalyzer(str(py_file))
            analyzer.visit(tree)
            
            for imported_module in analyzer.from_imports.keys():
                if not imported_module.startswith("app."):
                    continue
                
                # Determine imported module's layer
                imported_layer = None
                for layer, patterns in layers.items():
                    if any(pattern in imported_module for pattern in patterns):
                        imported_layer = layer
                        break
                
                if imported_layer and imported_layer not in allowed_deps.get(file_layer, []):
                    violations.append({
                        "file": rel_path,
                        "layer": file_layer,
                        "imports_from": imported_module,
                        "imported_layer": imported_layer,
                        "violation": f"{file_layer} should not depend on {imported_layer}",
                    })
        except Exception:
            pass
    
    return {
        "total_violations": len(violations),
        "violations": violations[:20],
    }


def main():
    """Main execution."""
    print("🏗️  Analyzing architecture and dependencies...")
    
    deps = analyze_dependencies("app")
    layers = analyze_layer_violations("app")
    
    print("\n" + "=" * 80)
    print("ARCHITECTURE ANALYSIS REPORT")
    print("=" * 80)
    
    print(f"\n📦 Total Modules: {deps['total_modules']}")
    print(f"\n🔗 Highly Coupled Modules (>15 dependencies):")
    for module, count in deps['highly_coupled'][:10]:
        print(f"  - {module}: {count} dependencies")
    
    print(f"\n🔄 Circular Dependencies Detected: {len(deps['circular_dependencies'])}")
    for mod1, mod2 in deps['circular_dependencies'][:5]:
        print(f"  - {mod1} ↔️ {mod2}")
    
    print(f"\n🏛️  Layer Violations: {layers['total_violations']}")
    for violation in layers['violations'][:5]:
        print(f"  - {violation['file']}")
        print(f"    {violation['violation']}")
    
    # Save report
    output = {
        "dependencies": deps,
        "layer_violations": layers,
    }
    
    with open("architecture_analysis.json", "w") as f:
        json.dump(output, f, indent=2)
    
    print(f"\n💾 Detailed report saved to: architecture_analysis.json")
    print("=" * 80)


if __name__ == "__main__":
    main()
