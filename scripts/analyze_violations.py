#!/usr/bin/env python3
"""
أداة تحليل انتهاكات SOLID + DRY + KISS
SOLID + DRY + KISS Violations Analyzer
"""

import ast
from collections import defaultdict
from pathlib import Path
from typing import NamedTuple


class Violation(NamedTuple):
    file: str
    line: int
    type: str
    description: str
    severity: str  # 'high', 'medium', 'low'


class CodeAnalyzer(ast.NodeVisitor):
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.violations = []
        self.functions = []
        self.classes = []
        self.any_count = 0
        self.old_typing_count = 0

    def visit_FunctionDef(self, node):
        # Check function length (KISS)
        func_lines = node.end_lineno - node.lineno
        if func_lines > 30:
            self.violations.append(
                Violation(
                    file=self.filepath,
                    line=node.lineno,
                    type="KISS",
                    description=f"Function '{node.name}' is too long ({func_lines} lines). Split into smaller functions.",
                    severity="medium",
                )
            )

        # Check number of parameters (KISS)
        if len(node.args.args) > 5:
            self.violations.append(
                Violation(
                    file=self.filepath,
                    line=node.lineno,
                    type="KISS",
                    description=f"Function '{node.name}' has {len(node.args.args)} parameters. Consider using a config object.",
                    severity="medium",
                )
            )

        # Check for Any type usage (SOLID - Interface Segregation)
        for arg in node.args.args:
            if getattr(arg, "annotation", None) and self._has_any_type(arg.annotation):
                self.any_count += 1
                self.violations.append(
                    Violation(
                        file=self.filepath,
                        line=node.lineno,
                        type="SOLID",
                        description=f"Function '{node.name}' uses Any type. Define specific types.",
                        severity="high",
                    )
                )

        self.functions.append(node.name)
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        # Check class size (KISS)
        class_lines = node.end_lineno - node.lineno
        if class_lines > 200:
            self.violations.append(
                Violation(
                    file=self.filepath,
                    line=node.lineno,
                    type="KISS",
                    description=f"Class '{node.name}' is too large ({class_lines} lines). Consider splitting.",
                    severity="high",
                )
            )

        # Count methods (Single Responsibility)
        methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
        if len(methods) > 15:
            self.violations.append(
                Violation(
                    file=self.filepath,
                    line=node.lineno,
                    type="SOLID",
                    description=f"Class '{node.name}' has {len(methods)} methods. May violate Single Responsibility Principle.",
                    severity="medium",
                )
            )

        self.classes.append(node.name)
        self.generic_visit(node)

    def visit_Import(self, node):
        # Check for old typing imports
        for _alias in node.names:
            if "typing" in node.module if hasattr(node, "module") else "":
                self.old_typing_count += 1
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        # Check for old typing imports
        if node.module == "typing":
            old_types = ["Optional", "Union", "List", "Dict", "Tuple", "Set", "Any"]
            for alias in node.names:
                if alias.name in old_types:
                    self.old_typing_count += 1
                    if alias.name == "Any":
                        self.violations.append(
                            Violation(
                                file=self.filepath,
                                line=node.lineno,
                                type="SOLID",
                                description="Import of 'Any' type. Use specific types instead.",
                                severity="high",
                            )
                        )
        self.generic_visit(node)

    def _has_any_type(self, node):
        """Check if node contains Any type"""
        if isinstance(node, ast.Name) and node.id == "Any":
            return True
        if isinstance(node, ast.Subscript):
            return self._has_any_type(node.value) or self._has_any_type(node.slice)
        return False


def analyze_file(filepath: Path) -> CodeAnalyzer:
    """Analyze a single Python file."""
    try:
        with open(filepath, encoding="utf-8") as f:
            content = f.read()

        tree = ast.parse(content, filename=str(filepath))
        analyzer = CodeAnalyzer(str(filepath))
        analyzer.visit(tree)
        return analyzer

    except Exception as e:
        print(f"❌ Error analyzing {filepath}: {e}")
        return CodeAnalyzer(str(filepath))


def main():
    """Main analysis function."""
    app_dir = Path("app")

    if not app_dir.exists():
        print("❌ app/ directory not found!")
        return

    print("🔍 Analyzing project for SOLID + DRY + KISS violations...\n")

    all_violations = []
    total_functions = 0
    total_classes = 0
    total_any = 0
    total_old_typing = 0

    python_files = list(app_dir.rglob("*.py"))

    for filepath in python_files:
        analyzer = analyze_file(filepath)
        all_violations.extend(analyzer.violations)
        total_functions += len(analyzer.functions)
        total_classes += len(analyzer.classes)
        total_any += analyzer.any_count
        total_old_typing += analyzer.old_typing_count

    # Group violations by type and severity
    violations_by_type = defaultdict(list)
    violations_by_severity = defaultdict(list)

    for v in all_violations:
        violations_by_type[v.type].append(v)
        violations_by_severity[v.severity].append(v)

    # Print summary
    print("=" * 70)
    print("📊 ANALYSIS SUMMARY")
    print("=" * 70)
    print(f"\n📁 Files analyzed: {len(python_files)}")
    print(f"🔧 Functions found: {total_functions}")
    print(f"📦 Classes found: {total_classes}")
    print(f"⚠️  Total violations: {len(all_violations)}")

    print(f"\n{'─' * 70}")
    print("VIOLATIONS BY TYPE:")
    print(f"{'─' * 70}")
    for vtype in ["SOLID", "DRY", "KISS"]:
        count = len(violations_by_type[vtype])
        print(f"  {vtype:10} : {count:4} violations")

    print(f"\n{'─' * 70}")
    print("VIOLATIONS BY SEVERITY:")
    print(f"{'─' * 70}")
    for severity in ["high", "medium", "low"]:
        count = len(violations_by_severity[severity])
        icon = "🔴" if severity == "high" else "🟡" if severity == "medium" else "🟢"
        print(f"  {icon} {severity.capitalize():10} : {count:4} violations")

    print(f"\n{'─' * 70}")
    print("TYPE SAFETY ISSUES:")
    print(f"{'─' * 70}")
    print(f"  ❌ 'Any' type usage: {total_any}")
    print(f"  📝 Old typing imports: {total_old_typing}")

    # Print top 10 violations
    print(f"\n{'=' * 70}")
    print("🔝 TOP 10 HIGH-SEVERITY VIOLATIONS:")
    print(f"{'=' * 70}\n")

    high_violations = violations_by_severity["high"][:10]
    for i, v in enumerate(high_violations, 1):
        print(f"{i}. [{v.type}] {v.file}:{v.line}")
        print(f"   {v.description}\n")

    print(f"\n{'=' * 70}")
    print("💡 RECOMMENDATIONS:")
    print(f"{'=' * 70}")
    print("1. Replace all 'Any' types with specific types")
    print("2. Split large functions (>30 lines) into smaller ones")
    print("3. Split large classes (>200 lines) into smaller ones")
    print("4. Reduce function parameters to <=5 using config objects")
    print("5. Apply Single Responsibility Principle to classes with >15 methods")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    main()
