#!/usr/bin/env python3
"""
SOLID Principles Analyzer
Analyzes codebase for violations of SOLID principles and complexity metrics.
"""
import ast
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any


class SOLIDAnalyzer(ast.NodeVisitor):
    """Analyzes Python code for SOLID violations."""

    def __init__(self):
        self.violations = []
        self.metrics = {
            "classes": 0,
            "methods": 0,
            "functions": 0,
            "lines": 0,
            "complexity": 0,
        }
        self.current_class = None
        self.class_responsibilities = defaultdict(list)
        self.class_dependencies = defaultdict(set)
        self.method_complexity = []

    def visit_ClassDef(self, node: ast.ClassDef):
        """Analyze class definitions for SRP and OCP violations."""
        self.metrics["classes"] += 1
        self.current_class = node.name

        # Count methods and analyze responsibilities
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        self.metrics["methods"] += len(methods)

        # Single Responsibility Principle check
        if len(methods) > 15:
            self.violations.append({
                "principle": "SRP",
                "class": node.name,
                "line": node.lineno,
                "severity": "high",
                "message": f"Class has {len(methods)} methods - likely violates SRP",
            })

        # Check for god objects (too many attributes)
        attributes = [n for n in node.body if isinstance(n, ast.Assign)]
        if len(attributes) > 10:
            self.violations.append({
                "principle": "SRP",
                "class": node.name,
                "line": node.lineno,
                "severity": "medium",
                "message": f"Class has {len(attributes)} attributes - possible god object",
            })

        # Analyze dependencies
        for item in ast.walk(node):
            if isinstance(item, ast.Import):
                for alias in item.names:
                    self.class_dependencies[node.name].add(alias.name)
            elif isinstance(item, ast.ImportFrom):
                if item.module:
                    self.class_dependencies[node.name].add(item.module)

        # Dependency Inversion Principle check
        if len(self.class_dependencies[node.name]) > 10:
            self.violations.append({
                "principle": "DIP",
                "class": node.name,
                "line": node.lineno,
                "severity": "medium",
                "message": f"Class has {len(self.class_dependencies[node.name])} dependencies - tight coupling",
            })

        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Analyze function complexity."""
        self.metrics["functions"] += 1

        # Calculate cyclomatic complexity (simplified)
        complexity = self._calculate_complexity(node)
        self.method_complexity.append({
            "name": f"{self.current_class}.{node.name}" if self.current_class else node.name,
            "complexity": complexity,
            "line": node.lineno,
        })

        if complexity > 10:
            self.violations.append({
                "principle": "SRP",
                "function": node.name,
                "class": self.current_class,
                "line": node.lineno,
                "severity": "high",
                "message": f"Function complexity {complexity} exceeds threshold (10)",
            })

        # Check function length
        func_lines = len(node.body)
        if func_lines > 50:
            self.violations.append({
                "principle": "SRP",
                "function": node.name,
                "class": self.current_class,
                "line": node.lineno,
                "severity": "medium",
                "message": f"Function has {func_lines} lines - too long",
            })

        # Check parameter count (ISP violation indicator)
        params = len(node.args.args)
        if params > 7:
            self.violations.append({
                "principle": "ISP",
                "function": node.name,
                "class": self.current_class,
                "line": node.lineno,
                "severity": "medium",
                "message": f"Function has {params} parameters - interface too fat",
            })

        self.generic_visit(node)

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1
        for item in ast.walk(node):
            if isinstance(item, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(item, ast.BoolOp):
                complexity += len(item.values) - 1
        return complexity


def analyze_file(filepath: Path) -> dict[str, Any]:
    """Analyze a single Python file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            tree = ast.parse(content, filename=str(filepath))

        analyzer = SOLIDAnalyzer()
        analyzer.visit(tree)
        analyzer.metrics["lines"] = len(content.splitlines())

        return {
            "file": str(filepath),
            "violations": analyzer.violations,
            "metrics": analyzer.metrics,
            "method_complexity": analyzer.method_complexity,
        }
    except Exception as e:
        return {
            "file": str(filepath),
            "error": str(e),
            "violations": [],
            "metrics": {},
            "method_complexity": [],
        }


def analyze_project(root_dir: str = "app") -> dict[str, Any]:
    """Analyze entire project."""
    results = {
        "total_violations": 0,
        "violations_by_principle": defaultdict(int),
        "violations_by_severity": defaultdict(int),
        "files_analyzed": 0,
        "total_metrics": defaultdict(int),
        "high_complexity_methods": [],
        "files": [],
    }

    root_path = Path(root_dir)
    for py_file in root_path.rglob("*.py"):
        if "__pycache__" in str(py_file) or "test_" in py_file.name:
            continue

        file_result = analyze_file(py_file)
        results["files"].append(file_result)
        results["files_analyzed"] += 1

        # Aggregate violations
        for violation in file_result.get("violations", []):
            results["total_violations"] += 1
            results["violations_by_principle"][violation["principle"]] += 1
            results["violations_by_severity"][violation["severity"]] += 1

        # Aggregate metrics
        for key, value in file_result.get("metrics", {}).items():
            results["total_metrics"][key] += value

        # Track high complexity methods
        for method in file_result.get("method_complexity", []):
            if method["complexity"] > 10:
                results["high_complexity_methods"].append({
                    "file": str(py_file),
                    **method,
                })

    return results


def main():
    """Main execution."""
    print("🔍 Analyzing codebase for SOLID violations and complexity...")

    results = analyze_project("app")

    # Print summary
    print("\n" + "=" * 80)
    print("SOLID ANALYSIS REPORT")
    print("=" * 80)
    print(f"\n📊 Files Analyzed: {results['files_analyzed']}")
    print(f"📏 Total Lines: {results['total_metrics']['lines']:,}")
    print(f"🏛️  Total Classes: {results['total_metrics']['classes']}")
    print(f"⚙️  Total Functions: {results['total_metrics']['functions']}")
    print(f"\n⚠️  Total Violations: {results['total_violations']}")

    print("\n📋 Violations by SOLID Principle:")
    for principle, count in sorted(results['violations_by_principle'].items()):
        principle_names = {
            "SRP": "Single Responsibility",
            "OCP": "Open/Closed",
            "LSP": "Liskov Substitution",
            "ISP": "Interface Segregation",
            "DIP": "Dependency Inversion",
        }
        print(f"  {principle} ({principle_names.get(principle, principle)}): {count}")

    print("\n🚨 Violations by Severity:")
    for severity, count in sorted(results['violations_by_severity'].items()):
        print(f"  {severity.upper()}: {count}")

    print(f"\n🔥 High Complexity Methods: {len(results['high_complexity_methods'])}")
    if results['high_complexity_methods']:
        print("\nTop 10 Most Complex Methods:")
        sorted_methods = sorted(
            results['high_complexity_methods'],
            key=lambda x: x['complexity'],
            reverse=True
        )[:10]
        for method in sorted_methods:
            print(f"  - {method['name']} (complexity: {method['complexity']}, line: {method['line']})")
            print(f"    File: {method['file']}")

    # Save detailed report
    output_file = "solid_analysis_report.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n💾 Detailed report saved to: {output_file}")
    print("=" * 80)

    return results


if __name__ == "__main__":
    main()
