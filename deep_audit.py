#!/usr/bin/env python3
"""
Deep Code Audit - Zero Tolerance for Complexity
Scans every file, function, class for clarity and purpose.
"""
import ast
import json
import os
from collections import defaultdict
from pathlib import Path
from typing import Any


class DeepAuditor(ast.NodeVisitor):
    """Deep code auditor - zero tolerance for complexity."""

    def __init__(self, filepath: str):
        self.filepath = filepath
        self.issues = []
        self.metrics = {
            "classes": 0,
            "functions": 0,
            "lines": 0,
            "docstrings": 0,
            "missing_docstrings": 0,
            "max_complexity": 0,
            "max_nesting": 0,
            "unused_imports": 0,
        }
        self.imports = set()
        self.used_names = set()
        self.current_nesting = 0
        self.max_nesting_seen = 0

    def visit_Import(self, node: ast.Import):
        """Track imports."""
        for alias in node.names:
            self.imports.add(alias.name.split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """Track from imports."""
        if node.module:
            self.imports.add(node.module.split(".")[0])
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name):
        """Track name usage."""
        self.used_names.add(node.id)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef):
        """Audit class definition."""
        self.metrics["classes"] += 1

        # Check docstring
        if not ast.get_docstring(node):
            self.metrics["missing_docstrings"] += 1
            self.issues.append({
                "type": "missing_docstring",
                "severity": "medium",
                "line": node.lineno,
                "message": f"Class '{node.name}' missing docstring",
            })
        else:
            self.metrics["docstrings"] += 1

        # Check method count (SRP)
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        if len(methods) > 10:
            self.issues.append({
                "type": "god_class",
                "severity": "high",
                "line": node.lineno,
                "message": f"Class '{node.name}' has {len(methods)} methods (max: 10)",
            })

        # Check for too many attributes
        assigns = [n for n in node.body if isinstance(n, ast.Assign)]
        if len(assigns) > 8:
            self.issues.append({
                "type": "too_many_attributes",
                "severity": "medium",
                "line": node.lineno,
                "message": f"Class '{node.name}' has {len(assigns)} attributes (max: 8)",
            })

        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """Audit function definition."""
        self.metrics["functions"] += 1

        # Check docstring
        if not ast.get_docstring(node):
            self.metrics["missing_docstrings"] += 1
            self.issues.append({
                "type": "missing_docstring",
                "severity": "low",
                "line": node.lineno,
                "message": f"Function '{node.name}' missing docstring",
            })
        else:
            self.metrics["docstrings"] += 1

        # Calculate complexity
        complexity = self._calculate_complexity(node)
        if complexity > self.metrics["max_complexity"]:
            self.metrics["max_complexity"] = complexity

        if complexity > 5:
            self.issues.append({
                "type": "high_complexity",
                "severity": "critical",
                "line": node.lineno,
                "message": f"Function '{node.name}' complexity {complexity} exceeds 5",
            })

        # Check function length
        func_lines = len(node.body)
        if func_lines > 30:
            self.issues.append({
                "type": "long_function",
                "severity": "high",
                "line": node.lineno,
                "message": f"Function '{node.name}' has {func_lines} lines (max: 30)",
            })

        # Check parameter count
        params = len(node.args.args)
        if params > 5:
            self.issues.append({
                "type": "too_many_params",
                "severity": "medium",
                "line": node.lineno,
                "message": f"Function '{node.name}' has {params} parameters (max: 5)",
            })

        # Check nesting depth
        max_nesting = self._calculate_max_nesting(node)
        if max_nesting > self.metrics["max_nesting"]:
            self.metrics["max_nesting"] = max_nesting

        if max_nesting > 3:
            self.issues.append({
                "type": "deep_nesting",
                "severity": "high",
                "line": node.lineno,
                "message": f"Function '{node.name}' has nesting depth {max_nesting} (max: 3)",
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

    def _calculate_max_nesting(self, node: ast.AST, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth."""
        max_depth = current_depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                child_depth = self._calculate_max_nesting(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._calculate_max_nesting(child, current_depth)
                max_depth = max(max_depth, child_depth)
        return max_depth


def audit_file(filepath: Path) -> dict[str, Any]:
    """Audit a single file."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            tree = ast.parse(content, filename=str(filepath))

        auditor = DeepAuditor(str(filepath))
        auditor.visit(tree)
        auditor.metrics["lines"] = len(content.splitlines())

        # Check for unused imports (simplified)
        # This is a basic check - real unused import detection is more complex
        # auditor.metrics["unused_imports"] = len(auditor.imports - auditor.used_names)

        return {
            "file": str(filepath),
            "issues": auditor.issues,
            "metrics": auditor.metrics,
        }
    except Exception as e:
        return {
            "file": str(filepath),
            "error": str(e),
            "issues": [],
            "metrics": {},
        }


def deep_audit(root_dir: str = "app") -> dict[str, Any]:
    """Perform deep audit of entire codebase."""
    results = {
        "total_files": 0,
        "total_issues": 0,
        "issues_by_type": defaultdict(int),
        "issues_by_severity": defaultdict(int),
        "critical_issues": [],
        "files_with_issues": [],
        "clean_files": [],
        "aggregate_metrics": defaultdict(int),
    }

    root_path = Path(root_dir)
    for py_file in sorted(root_path.rglob("*.py")):
        if "__pycache__" in str(py_file) or "test_" in py_file.name:
            continue

        file_result = audit_file(py_file)
        results["total_files"] += 1

        # Aggregate metrics
        for key, value in file_result.get("metrics", {}).items():
            if key.startswith("max_"):
                results["aggregate_metrics"][key] = max(
                    results["aggregate_metrics"][key], value
                )
            else:
                results["aggregate_metrics"][key] += value

        # Process issues
        issues = file_result.get("issues", [])
        if issues:
            results["files_with_issues"].append({
                "file": str(py_file),
                "issue_count": len(issues),
                "issues": issues,
            })
            results["total_issues"] += len(issues)

            for issue in issues:
                results["issues_by_type"][issue["type"]] += 1
                results["issues_by_severity"][issue["severity"]] += 1

                if issue["severity"] == "critical":
                    results["critical_issues"].append({
                        "file": str(py_file),
                        **issue,
                    })
        else:
            results["clean_files"].append(str(py_file))

    return results


def main():
    """Main execution."""
    print("🔍 Deep Code Audit - Zero Tolerance for Complexity")
    print("=" * 80)

    results = deep_audit("app")

    # Print summary
    print(f"\n📊 Files Audited: {results['total_files']}")
    print(f"✅ Clean Files: {len(results['clean_files'])}")
    print(f"⚠️  Files with Issues: {len(results['files_with_issues'])}")
    print(f"🚨 Total Issues: {results['total_issues']}")

    print("\n📋 Issues by Type:")
    for issue_type, count in sorted(results['issues_by_type'].items(), key=lambda x: -x[1]):
        print(f"  {issue_type}: {count}")

    print("\n🚨 Issues by Severity:")
    for severity, count in sorted(results['issues_by_severity'].items()):
        print(f"  {severity.upper()}: {count}")

    print("\n📈 Aggregate Metrics:")
    print(f"  Total Classes: {results['aggregate_metrics']['classes']}")
    print(f"  Total Functions: {results['aggregate_metrics']['functions']}")
    print(f"  Total Lines: {results['aggregate_metrics']['lines']:,}")
    print(f"  Docstrings: {results['aggregate_metrics']['docstrings']}")
    print(f"  Missing Docstrings: {results['aggregate_metrics']['missing_docstrings']}")
    print(f"  Max Complexity: {results['aggregate_metrics']['max_complexity']}")
    print(f"  Max Nesting: {results['aggregate_metrics']['max_nesting']}")

    if results['critical_issues']:
        print(f"\n🔥 Critical Issues ({len(results['critical_issues'])}):")
        for issue in results['critical_issues'][:10]:
            print(f"  - {issue['file']}:{issue['line']}")
            print(f"    {issue['message']}")

    # Calculate cleanliness score
    total_possible_issues = results['total_files'] * 10  # Arbitrary baseline
    cleanliness_score = max(0, 100 - (results['total_issues'] / total_possible_issues * 100))
    print(f"\n🎯 Cleanliness Score: {cleanliness_score:.1f}%")

    # Save detailed report
    output_file = "deep_audit_report.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n💾 Detailed report saved to: {output_file}")
    print("=" * 80)

    return results


if __name__ == "__main__":
    main()
