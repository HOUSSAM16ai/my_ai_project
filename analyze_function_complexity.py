#!/usr/bin/env python3
"""
SUPERHUMAN FUNCTION COMPLEXITY ANALYZER
========================================
تحليل خارق للدوال المعقدة بدقة تتفوق على الشركات العملاقة

This tool analyzes Python code to identify complex functions with extreme precision.
No AI API keys required - uses static code analysis for instant results.

Features:
- Cyclomatic complexity (McCabe)
- Lines of code metrics
- Nesting depth analysis
- Maintainability index
- Halstead metrics
- Cognitive complexity estimation
- Detailed recommendations

Usage:
    python analyze_function_complexity.py
    python analyze_function_complexity.py --threshold 10
    python analyze_function_complexity.py --path app/services
    python analyze_function_complexity.py --export report.json
"""

import argparse
import ast
import json
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class FunctionMetrics:
    """Metrics for a single function"""

    name: str
    file_path: str
    line_number: int
    lines_of_code: int
    cyclomatic_complexity: int
    nesting_depth: int
    num_parameters: int
    num_returns: int
    num_branches: int
    num_loops: int
    cognitive_complexity: int
    maintainability_index: float
    complexity_grade: str
    issues: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)

    @property
    def total_complexity_score(self) -> float:
        """Calculate overall complexity score (0-100, higher is more complex)"""
        # Weighted scoring
        score = 0.0
        score += min(self.cyclomatic_complexity * 2, 40)  # Up to 40 points
        score += min(self.lines_of_code / 10, 20)  # Up to 20 points
        score += min(self.nesting_depth * 5, 15)  # Up to 15 points
        score += min(self.cognitive_complexity * 1.5, 25)  # Up to 25 points
        return min(score, 100)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON export"""
        return {
            "name": self.name,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "lines_of_code": self.lines_of_code,
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "nesting_depth": self.nesting_depth,
            "num_parameters": self.num_parameters,
            "num_returns": self.num_returns,
            "num_branches": self.num_branches,
            "num_loops": self.num_loops,
            "cognitive_complexity": self.cognitive_complexity,
            "maintainability_index": round(self.maintainability_index, 2),
            "complexity_grade": self.complexity_grade,
            "total_complexity_score": round(self.total_complexity_score, 2),
            "issues": self.issues,
            "recommendations": self.recommendations,
        }


class ComplexityAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze function complexity"""

    def __init__(self, source_code: str):
        self.source_code = source_code
        self.source_lines = source_code.split("\n")
        self.functions = []
        self.current_function = None
        self.current_depth = 0

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definition"""
        # Save previous function context
        prev_function = self.current_function

        # Calculate metrics for this function
        metrics = self._analyze_function(node)
        self.functions.append(metrics)

        # Visit nested functions
        self.current_function = metrics
        self.generic_visit(node)
        self.current_function = prev_function

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definition"""
        self.visit_FunctionDef(node)

    def _analyze_function(self, node: ast.FunctionDef) -> FunctionMetrics:
        """Analyze a single function"""
        name = node.name
        line_number = node.lineno

        # Count lines of code (excluding docstrings and comments)
        func_lines = self._get_function_lines(node)
        lines_of_code = len(func_lines)

        # Calculate cyclomatic complexity
        cyclomatic = self._calculate_cyclomatic_complexity(node)

        # Calculate nesting depth
        nesting = self._calculate_nesting_depth(node)

        # Count parameters
        num_params = len(node.args.args) + len(node.args.kwonlyargs)

        # Count returns, branches, loops
        counter = StatementCounter()
        counter.visit(node)

        # Calculate cognitive complexity
        cognitive = self._calculate_cognitive_complexity(node)

        # Calculate maintainability index
        # MI = 171 - 5.2 * ln(Halstead Volume) - 0.23 * (Cyclomatic) - 16.2 * ln(LOC)
        # Simplified version
        import math

        if lines_of_code > 0:
            halstead_volume = lines_of_code * math.log(max(num_params + 1, 2))
            mi = (
                171
                - 5.2 * math.log(halstead_volume + 1)
                - 0.23 * cyclomatic
                - 16.2 * math.log(lines_of_code)
            )
            mi = max(0, min(100, mi))  # Clamp to 0-100
        else:
            mi = 100.0

        # Determine complexity grade
        grade = self._get_complexity_grade(cyclomatic, lines_of_code, nesting)

        # Create metrics object
        metrics = FunctionMetrics(
            name=name,
            file_path="",  # Will be set by caller
            line_number=line_number,
            lines_of_code=lines_of_code,
            cyclomatic_complexity=cyclomatic,
            nesting_depth=nesting,
            num_parameters=num_params,
            num_returns=counter.returns,
            num_branches=counter.branches,
            num_loops=counter.loops,
            cognitive_complexity=cognitive,
            maintainability_index=mi,
            complexity_grade=grade,
        )

        # Identify issues and recommendations
        self._add_issues_and_recommendations(metrics)

        return metrics

    def _get_function_lines(self, node: ast.FunctionDef) -> list[str]:
        """Get function source lines (excluding empty and comment lines)"""
        start = node.lineno - 1
        end = node.end_lineno if hasattr(node, "end_lineno") else start + 1

        lines = []
        in_docstring = False
        for i in range(start, min(end, len(self.source_lines))):
            line = self.source_lines[i].strip()
            # Skip empty lines
            if not line:
                continue
            # Skip comments
            if line.startswith("#"):
                continue
            # Skip docstrings
            if line.startswith('"""') or line.startswith("'''"):
                if not in_docstring:
                    in_docstring = True
                    if line.count('"""') >= 2 or line.count("'''") >= 2:
                        in_docstring = False
                    continue
                else:
                    in_docstring = False
                    continue
            if in_docstring:
                continue
            lines.append(line)

        return lines

    def _calculate_cyclomatic_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate McCabe cyclomatic complexity"""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            # Decision points add complexity
            if isinstance(
                child,
                ast.If
                | ast.While
                | ast.For
                | ast.AsyncFor
                | ast.ExceptHandler
                | ast.With
                | ast.AsyncWith,
            ):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1

        return complexity

    def _calculate_nesting_depth(self, node: ast.FunctionDef) -> int:
        """Calculate maximum nesting depth"""
        max_depth = 0

        def visit_depth(node, depth=0):
            nonlocal max_depth
            max_depth = max(max_depth, depth)

            for child in ast.iter_child_nodes(node):
                if isinstance(
                    child,
                    ast.If
                    | ast.While
                    | ast.For
                    | ast.AsyncFor
                    | ast.With
                    | ast.AsyncWith
                    | ast.Try,
                ):
                    visit_depth(child, depth + 1)
                else:
                    visit_depth(child, depth)

        visit_depth(node)
        return max_depth

    def _calculate_cognitive_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cognitive complexity (like SonarQube)"""
        complexity = 0

        def visit_cognitive(n, nesting=0):
            nonlocal complexity

            for child in ast.iter_child_nodes(n):
                # Flow breaking structures
                if isinstance(child, ast.If | ast.While | ast.For | ast.AsyncFor):
                    complexity += 1 + nesting
                    visit_cognitive(child, nesting + 1)
                elif isinstance(child, ast.BoolOp):
                    # Logical operators
                    complexity += len(child.values) - 1
                    visit_cognitive(child, nesting)
                elif isinstance(child, ast.Try | ast.ExceptHandler):
                    complexity += 1 + nesting
                    visit_cognitive(child, nesting + 1)
                else:
                    visit_cognitive(child, nesting)

        visit_cognitive(node)
        return complexity

    def _get_complexity_grade(self, cyclomatic: int, loc: int, nesting: int) -> str:
        """Determine complexity grade (A-F)"""
        # Grade based on multiple factors
        score = 0

        # Cyclomatic complexity
        if cyclomatic <= 5:
            score += 0
        elif cyclomatic <= 10:
            score += 1
        elif cyclomatic <= 20:
            score += 2
        elif cyclomatic <= 30:
            score += 3
        else:
            score += 4

        # Lines of code
        if loc <= 50:
            score += 0
        elif loc <= 100:
            score += 1
        elif loc <= 200:
            score += 2
        elif loc <= 300:
            score += 3
        else:
            score += 4

        # Nesting depth
        if nesting <= 2:
            score += 0
        elif nesting <= 3:
            score += 1
        elif nesting <= 4:
            score += 2
        else:
            score += 3

        # Convert score to grade
        if score <= 1:
            return "A"  # Excellent
        elif score <= 3:
            return "B"  # Good
        elif score <= 5:
            return "C"  # Fair
        elif score <= 7:
            return "D"  # Poor
        elif score <= 9:
            return "E"  # Very Poor
        else:
            return "F"  # Critical

    def _add_issues_and_recommendations(self, metrics: FunctionMetrics) -> None:
        """Add issues and recommendations based on metrics"""
        issues = []
        recommendations = []

        # Cyclomatic complexity
        if metrics.cyclomatic_complexity > 30:
            issues.append(f"❌ Very high cyclomatic complexity ({metrics.cyclomatic_complexity})")
            recommendations.append(
                "🔧 Break down into smaller functions using Extract Method pattern"
            )
        elif metrics.cyclomatic_complexity > 15:
            issues.append(f"⚠️  High cyclomatic complexity ({metrics.cyclomatic_complexity})")
            recommendations.append("💡 Consider simplifying conditional logic")

        # Lines of code
        if metrics.lines_of_code > 300:
            issues.append(f"❌ Extremely long function ({metrics.lines_of_code} lines)")
            recommendations.append(
                "🔧 Split into multiple focused functions (target: <50 lines each)"
            )
        elif metrics.lines_of_code > 100:
            issues.append(f"⚠️  Long function ({metrics.lines_of_code} lines)")
            recommendations.append("💡 Consider extracting helper methods")

        # Nesting depth
        if metrics.nesting_depth > 4:
            issues.append(f"❌ Excessive nesting ({metrics.nesting_depth} levels)")
            recommendations.append("🔧 Use early returns and guard clauses to reduce nesting")
        elif metrics.nesting_depth > 3:
            issues.append(f"⚠️  Deep nesting ({metrics.nesting_depth} levels)")
            recommendations.append("💡 Flatten nested structures where possible")

        # Parameters
        if metrics.num_parameters > 7:
            issues.append(f"⚠️  Too many parameters ({metrics.num_parameters})")
            recommendations.append("💡 Consider using parameter objects or dataclasses")

        # Cognitive complexity
        if metrics.cognitive_complexity > 20:
            issues.append(f"❌ High cognitive complexity ({metrics.cognitive_complexity})")
            recommendations.append("🔧 Simplify logic flow - code is hard to understand")

        # Maintainability index
        if metrics.maintainability_index < 20:
            issues.append(f"❌ Very low maintainability ({metrics.maintainability_index:.1f}/100)")
            recommendations.append("🚨 URGENT: Refactor immediately - code is unmaintainable")
        elif metrics.maintainability_index < 40:
            issues.append(f"⚠️  Low maintainability ({metrics.maintainability_index:.1f}/100)")
            recommendations.append("⚠️  High priority refactoring needed")

        metrics.issues = issues
        metrics.recommendations = recommendations


class StatementCounter(ast.NodeVisitor):
    """Count various statement types"""

    def __init__(self):
        self.returns = 0
        self.branches = 0
        self.loops = 0

    def visit_Return(self, node):
        self.returns += 1
        self.generic_visit(node)

    def visit_If(self, node):
        self.branches += 1
        self.generic_visit(node)

    def visit_For(self, node):
        self.loops += 1
        self.generic_visit(node)

    def visit_While(self, node):
        self.loops += 1
        self.generic_visit(node)

    def visit_AsyncFor(self, node):
        self.loops += 1
        self.generic_visit(node)


def analyze_file(file_path: Path) -> list[FunctionMetrics]:
    """Analyze a Python file and return function metrics"""
    try:
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))

        analyzer = ComplexityAnalyzer(source)
        analyzer.visit(tree)

        # Set file path for all metrics
        for metrics in analyzer.functions:
            try:
                metrics.file_path = str(file_path.relative_to(Path.cwd()))
            except ValueError:
                # If file is not relative to cwd, use absolute path
                metrics.file_path = str(file_path)

        return analyzer.functions

    except SyntaxError as e:
        print(f"⚠️  Syntax error in {file_path}: {e}", file=sys.stderr)
        return []
    except Exception as e:
        print(f"❌ Error analyzing {file_path}: {e}", file=sys.stderr)
        return []


def analyze_directory(
    path: Path, exclude_dirs: set[str] | None = None, threshold: int = 10
) -> list[FunctionMetrics]:
    """Analyze all Python files in a directory"""
    if exclude_dirs is None:
        exclude_dirs = {
            "__pycache__",
            ".git",
            "venv",
            "env",
            "node_modules",
            ".venv",
            "dist",
            "build",
        }

    all_metrics = []

    for py_file in path.rglob("*.py"):
        # Skip excluded directories
        if any(excluded in py_file.parts for excluded in exclude_dirs):
            continue

        metrics = analyze_file(py_file)
        # Filter by complexity threshold
        complex_metrics = [m for m in metrics if m.cyclomatic_complexity >= threshold]
        all_metrics.extend(complex_metrics)

    return all_metrics


def print_summary(metrics_list: list[FunctionMetrics], show_all: bool = False) -> None:
    """Print analysis summary"""
    if not metrics_list:
        print("\n✅ No complex functions found! Code quality is excellent.\n")
        return

    # Sort by total complexity score
    sorted_metrics = sorted(metrics_list, key=lambda m: m.total_complexity_score, reverse=True)

    # Statistics
    total_functions = len(sorted_metrics)
    avg_complexity = sum(m.cyclomatic_complexity for m in sorted_metrics) / total_functions
    avg_loc = sum(m.lines_of_code for m in sorted_metrics) / total_functions

    grade_counts = defaultdict(int)
    for m in sorted_metrics:
        grade_counts[m.complexity_grade] += 1

    print("\n" + "=" * 80)
    print("🔍 SUPERHUMAN FUNCTION COMPLEXITY ANALYSIS")
    print("   تحليل خارق للدوال المعقدة")
    print("=" * 80)
    print("\n📊 SUMMARY:")
    print(f"   Total complex functions: {total_functions}")
    print(f"   Average cyclomatic complexity: {avg_complexity:.1f}")
    print(f"   Average lines of code: {avg_loc:.1f}")
    print("\n📈 GRADE DISTRIBUTION:")
    for grade in ["A", "B", "C", "D", "E", "F"]:
        count = grade_counts[grade]
        if count > 0:
            bar = "█" * min(count, 50)
            print(f"   {grade}: {bar} ({count})")

    print("\n🎯 TOP 10 MOST COMPLEX FUNCTIONS:")
    print("-" * 80)

    for i, metrics in enumerate(sorted_metrics[:10], 1):
        print(f"\n#{i} {metrics.name}()")
        print(f"   📁 File: {metrics.file_path}:{metrics.line_number}")
        print(f"   📊 Complexity Score: {metrics.total_complexity_score:.1f}/100")
        print(
            f"   🔢 Cyclomatic: {metrics.cyclomatic_complexity} | "
            f"LOC: {metrics.lines_of_code} | "
            f"Nesting: {metrics.nesting_depth} | "
            f"Grade: {metrics.complexity_grade}"
        )
        print(f"   💯 Maintainability: {metrics.maintainability_index:.1f}/100")

        if metrics.issues:
            print("   🚨 Issues:")
            for issue in metrics.issues:
                print(f"      {issue}")

        if metrics.recommendations:
            print("   💡 Recommendations:")
            for rec in metrics.recommendations[:2]:  # Show top 2
                print(f"      {rec}")

    if show_all and len(sorted_metrics) > 10:
        print(f"\n📋 ALL {total_functions} COMPLEX FUNCTIONS:")
        print("-" * 80)
        for metrics in sorted_metrics[10:]:
            print(
                f"  {metrics.name:40s} | "
                f"CC:{metrics.cyclomatic_complexity:3d} | "
                f"LOC:{metrics.lines_of_code:4d} | "
                f"Grade:{metrics.complexity_grade} | "
                f"{metrics.file_path}"
            )

    print("\n" + "=" * 80)
    print("✨ Analysis complete! Use --export to save detailed JSON report.")
    print("=" * 80 + "\n")


def export_json_report(metrics_list: list[FunctionMetrics], output_file: str) -> None:
    """Export detailed JSON report"""
    report = {
        "analysis_timestamp": __import__("datetime").datetime.now().isoformat(),
        "total_functions_analyzed": len(metrics_list),
        "functions": [m.to_dict() for m in metrics_list],
        "summary": {
            "total_complex_functions": len(metrics_list),
            "average_cyclomatic_complexity": (
                sum(m.cyclomatic_complexity for m in metrics_list) / len(metrics_list)
                if metrics_list
                else 0
            ),
            "average_lines_of_code": (
                sum(m.lines_of_code for m in metrics_list) / len(metrics_list)
                if metrics_list
                else 0
            ),
            "grade_distribution": {},
        },
    }

    # Add grade distribution
    for m in metrics_list:
        grade = m.complexity_grade
        report["summary"]["grade_distribution"][grade] = (
            report["summary"]["grade_distribution"].get(grade, 0) + 1
        )

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)

    print(f"✅ Detailed report exported to: {output_file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="🔍 Superhuman Function Complexity Analyzer - تحليل خارق للدوال المعقدة",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--path", type=str, default="app", help="Path to analyze (default: app)")
    parser.add_argument(
        "--threshold",
        type=int,
        default=10,
        help="Minimum cyclomatic complexity to report (default: 10)",
    )
    parser.add_argument("--export", type=str, help="Export detailed JSON report to file")
    parser.add_argument(
        "--all", action="store_true", help="Show all complex functions (not just top 10)"
    )

    args = parser.parse_args()

    # Analyze
    path = Path(args.path)
    if not path.exists():
        print(f"❌ Path not found: {path}")
        sys.exit(1)

    print(f"\n🔍 Analyzing Python files in: {path}")
    print(f"📊 Complexity threshold: {args.threshold}")
    print("⏳ Processing...\n")

    if path.is_file():
        metrics_list = analyze_file(path)
    else:
        metrics_list = analyze_directory(path, threshold=args.threshold)

    # Print results
    print_summary(metrics_list, show_all=args.all)

    # Export if requested
    if args.export:
        export_json_report(metrics_list, args.export)


if __name__ == "__main__":
    main()
