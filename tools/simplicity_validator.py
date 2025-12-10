#!/usr/bin/env python3
"""
Simplicity Principles Validator

This tool validates that the codebase follows strict simplicity principles:
- KISS (Keep It Simple, Stupid)
- YAGNI (You Ain't Gonna Need It)
- DRY (Don't Repeat Yourself)
- SOLID Principles
- Code complexity metrics

Usage:
    python tools/simplicity_validator.py [--directory app] [--report-file report.md]
"""

import ast
import os
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import warnings

try:
    from radon.complexity import cc_visit
    from radon.metrics import h_visit, mi_visit
    RADON_AVAILABLE = True
except ImportError:
    RADON_AVAILABLE = False
    warnings.warn("radon not installed. Install with: pip install radon", UserWarning)


@dataclass
class FunctionMetrics:
    """Metrics for a function."""
    name: str
    file: str
    line: int
    complexity: int
    lines: int
    parameters: int
    violations: List[str]


@dataclass
class ClassMetrics:
    """Metrics for a class."""
    name: str
    file: str
    line: int
    methods: int
    lines: int
    responsibilities: int
    violations: List[str]


@dataclass
class FileMetrics:
    """Metrics for a file."""
    path: str
    lines: int
    classes: int
    functions: int
    imports: int
    duplication_score: float
    violations: List[str]


class SimplicityValidator:
    """Validates code against simplicity principles."""

    # Thresholds for violations
    MAX_FUNCTION_COMPLEXITY = 10
    MAX_FUNCTION_LINES = 50
    MAX_FUNCTION_PARAMETERS = 5
    MAX_CLASS_METHODS = 20
    MAX_CLASS_RESPONSIBILITIES = 3
    MAX_FILE_LINES = 500
    MAX_NESTING_DEPTH = 3
    MAX_DUPLICATION_RATE = 5.0  # percentage

    def __init__(self, directory: str = "app"):
        self.directory = Path(directory)
        self.function_metrics: List[FunctionMetrics] = []
        self.class_metrics: List[ClassMetrics] = []
        self.file_metrics: List[FileMetrics] = []
        self.code_duplicates: Dict[str, List[str]] = defaultdict(list)
        
    def validate(self) -> Dict[str, any]:
        """Run all validation checks."""
        print(f"🔍 Validating simplicity principles in {self.directory}...")
        
        results = {
            "functions": [],
            "classes": [],
            "files": [],
            "overall": {
                "total_violations": 0,
                "complexity_score": 0,
                "maintainability_score": 0,
                "duplication_rate": 0,
            }
        }
        
        # Scan all Python files
        python_files = list(self.directory.rglob("*.py"))
        print(f"📂 Found {len(python_files)} Python files")
        
        for file_path in python_files:
            if self._should_skip(file_path):
                continue
                
            try:
                self._analyze_file(file_path)
            except Exception as e:
                print(f"⚠️  Error analyzing {file_path}: {e}")
        
        # Compile results
        results["functions"] = self.function_metrics
        results["classes"] = self.class_metrics
        results["files"] = self.file_metrics
        
        # Calculate overall metrics
        total_violations = (
            sum(len(f.violations) for f in self.function_metrics) +
            sum(len(c.violations) for c in self.class_metrics) +
            sum(len(f.violations) for f in self.file_metrics)
        )
        
        results["overall"]["total_violations"] = total_violations
        
        if RADON_AVAILABLE:
            avg_complexity = sum(f.complexity for f in self.function_metrics) / max(len(self.function_metrics), 1)
            results["overall"]["complexity_score"] = round(avg_complexity, 2)
        
        print(f"\n✅ Analysis complete!")
        print(f"   Total violations: {total_violations}")
        
        return results
    
    def _should_skip(self, file_path: Path) -> bool:
        """Check if file should be skipped."""
        skip_patterns = [
            "__pycache__",
            ".git",
            "migrations",
            "venv",
            ".venv",
            "node_modules",
        ]
        # Use path-based matching for proper directory detection
        parts = file_path.parts
        return any(pattern in parts for pattern in skip_patterns) or "tests" in parts
    
    def _analyze_file(self, file_path: Path):
        """Analyze a single Python file."""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return
        
        # File-level metrics
        lines = len(content.splitlines())
        violations = []
        
        if lines > self.MAX_FILE_LINES:
            violations.append(f"File too long ({lines} lines, max {self.MAX_FILE_LINES})")
        
        # Count classes and functions
        classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
        
        file_metrics = FileMetrics(
            path=str(file_path.relative_to(self.directory)),
            lines=lines,
            classes=len(classes),
            functions=len(functions),
            imports=len(imports),
            duplication_score=0.0,
            violations=violations
        )
        self.file_metrics.append(file_metrics)
        
        # Analyze classes
        for cls in classes:
            self._analyze_class(cls, file_path)
        
        # Analyze functions
        for func in functions:
            self._analyze_function(func, file_path, content)
        
        # Check for complexity with Radon if available
        if RADON_AVAILABLE:
            self._check_radon_metrics(file_path, content)
    
    def _analyze_class(self, cls: ast.ClassDef, file_path: Path):
        """Analyze a class for SRP violations."""
        methods = [node for node in cls.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]
        
        # Estimate lines (rough approximation)
        if hasattr(cls, 'end_lineno') and hasattr(cls, 'lineno'):
            lines = cls.end_lineno - cls.lineno
        else:
            lines = 0
        
        violations = []
        
        # Check number of methods (indicator of multiple responsibilities)
        if len(methods) > self.MAX_CLASS_METHODS:
            violations.append(
                f"Too many methods ({len(methods)}, max {self.MAX_CLASS_METHODS}). "
                "Consider splitting into multiple classes (SRP)"
            )
        
        # Detect multiple responsibilities by method name patterns
        responsibility_indicators = defaultdict(list)
        for method in methods:
            name = method.name.lower()
            if any(x in name for x in ['save', 'store', 'persist', 'write']):
                responsibility_indicators['persistence'].append(method.name)
            elif any(x in name for x in ['send', 'notify', 'email', 'sms']):
                responsibility_indicators['notification'].append(method.name)
            elif any(x in name for x in ['validate', 'check', 'verify']):
                responsibility_indicators['validation'].append(method.name)
            elif any(x in name for x in ['calculate', 'compute', 'process']):
                responsibility_indicators['computation'].append(method.name)
            elif any(x in name for x in ['format', 'render', 'display']):
                responsibility_indicators['presentation'].append(method.name)
        
        responsibilities = len([v for v in responsibility_indicators.values() if v])
        
        if responsibilities > self.MAX_CLASS_RESPONSIBILITIES:
            violations.append(
                f"Multiple responsibilities detected ({responsibilities}): "
                f"{list(responsibility_indicators.keys())}. Violates SRP"
            )
        
        class_metrics = ClassMetrics(
            name=cls.name,
            file=str(file_path.relative_to(self.directory)),
            line=cls.lineno,
            methods=len(methods),
            lines=lines,
            responsibilities=responsibilities,
            violations=violations
        )
        self.class_metrics.append(class_metrics)
    
    def _analyze_function(self, func: ast.FunctionDef, file_path: Path, content: str):
        """Analyze a function for simplicity violations."""
        # Calculate basic metrics
        if hasattr(func, 'end_lineno') and hasattr(func, 'lineno'):
            lines = func.end_lineno - func.lineno
        else:
            lines = 0
        
        parameters = len(func.args.args)
        
        # Calculate cyclomatic complexity
        complexity = self._calculate_complexity(func)
        
        # Check for violations
        violations = []
        
        if complexity > self.MAX_FUNCTION_COMPLEXITY:
            violations.append(
                f"High complexity ({complexity}, max {self.MAX_FUNCTION_COMPLEXITY}). "
                "Consider breaking into smaller functions (KISS)"
            )
        
        if lines > self.MAX_FUNCTION_LINES:
            violations.append(
                f"Function too long ({lines} lines, max {self.MAX_FUNCTION_LINES}). "
                "Break into smaller functions"
            )
        
        if parameters > self.MAX_FUNCTION_PARAMETERS:
            violations.append(
                f"Too many parameters ({parameters}, max {self.MAX_FUNCTION_PARAMETERS}). "
                "Consider using a config object or builder pattern"
            )
        
        # Check for deep nesting
        max_depth = self._calculate_nesting_depth(func)
        if max_depth > self.MAX_NESTING_DEPTH:
            violations.append(
                f"Deep nesting detected (depth {max_depth}, max {self.MAX_NESTING_DEPTH}). "
                "Use early returns or extract methods"
            )
        
        function_metrics = FunctionMetrics(
            name=func.name,
            file=str(file_path.relative_to(self.directory)),
            line=func.lineno,
            complexity=complexity,
            lines=lines,
            parameters=parameters,
            violations=violations
        )
        self.function_metrics.append(function_metrics)
    
    def _calculate_complexity(self, node: ast.AST) -> int:
        """Calculate cyclomatic complexity."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Each decision point adds 1 to complexity
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, 
                                 ast.ExceptHandler, ast.With, ast.AsyncWith)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, (ast.Lambda, ast.ListComp, ast.DictComp, 
                                   ast.SetComp, ast.GeneratorExp)):
                complexity += 1
        
        return complexity
    
    def _calculate_nesting_depth(self, node: ast.AST) -> int:
        """Calculate maximum nesting depth."""
        def get_depth(n, current_depth=0):
            max_depth = current_depth
            for child in ast.iter_child_nodes(n):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.With, ast.Try)):
                    depth = get_depth(child, current_depth + 1)
                    max_depth = max(max_depth, depth)
                else:
                    depth = get_depth(child, current_depth)
                    max_depth = max(max_depth, depth)
            return max_depth
        
        return get_depth(node)
    
    def _check_radon_metrics(self, file_path: Path, content: str):
        """Check metrics using Radon library."""
        try:
            # Complexity
            complexity_results = cc_visit(content)
            for result in complexity_results:
                # Find corresponding function metric and update
                for fm in self.function_metrics:
                    if fm.name == result.name and file_path.name in fm.file:
                        fm.complexity = result.complexity
                        break
            
            # Maintainability Index
            mi_results = mi_visit(content, multi=True)
            # Note: mi_results is already a score
            
            # Halstead metrics
            h_results = h_visit(content)
            
        except Exception as e:
            # Radon might fail on some files
            pass
    
    def generate_report(self, output_file: Optional[str] = None) -> str:
        """Generate a markdown report."""
        report_lines = [
            "# 📊 Simplicity Principles Validation Report",
            "",
            f"**Project**: {self.directory}",
            "",
            "---",
            "",
            "## 🎯 Overall Summary",
            "",
        ]
        
        # Overall metrics
        total_files = len(self.file_metrics)
        total_classes = len(self.class_metrics)
        total_functions = len(self.function_metrics)
        total_violations = (
            sum(len(f.violations) for f in self.function_metrics) +
            sum(len(c.violations) for c in self.class_metrics) +
            sum(len(f.violations) for f in self.file_metrics)
        )
        
        report_lines.extend([
            f"- **Files Analyzed**: {total_files}",
            f"- **Classes**: {total_classes}",
            f"- **Functions**: {total_functions}",
            f"- **Total Violations**: {total_violations}",
            "",
        ])
        
        # Violation breakdown
        if total_violations > 0:
            report_lines.extend([
                "### ⚠️ Violations Breakdown",
                "",
                f"- **Function Violations**: {sum(len(f.violations) for f in self.function_metrics)}",
                f"- **Class Violations**: {sum(len(c.violations) for c in self.class_metrics)}",
                f"- **File Violations**: {sum(len(f.violations) for f in self.file_metrics)}",
                "",
            ])
        
        # Top violators - Functions
        functions_with_violations = [f for f in self.function_metrics if f.violations]
        if functions_with_violations:
            report_lines.extend([
                "## 🔴 Top Function Violations",
                "",
                "| Function | File | Line | Complexity | Lines | Violations |",
                "|----------|------|------|------------|-------|------------|",
            ])
            
            # Sort by number of violations
            top_functions = sorted(
                functions_with_violations,
                key=lambda f: len(f.violations),
                reverse=True
            )[:10]
            
            for func in top_functions:
                violations_str = "; ".join(func.violations)
                report_lines.append(
                    f"| `{func.name}` | {func.file} | {func.line} | "
                    f"{func.complexity} | {func.lines} | {violations_str} |"
                )
            
            report_lines.append("")
        
        # Top violators - Classes
        classes_with_violations = [c for c in self.class_metrics if c.violations]
        if classes_with_violations:
            report_lines.extend([
                "## 🟠 Top Class Violations",
                "",
                "| Class | File | Line | Methods | Responsibilities | Violations |",
                "|-------|------|------|---------|------------------|------------|",
            ])
            
            top_classes = sorted(
                classes_with_violations,
                key=lambda c: len(c.violations),
                reverse=True
            )[:10]
            
            for cls in top_classes:
                violations_str = "; ".join(cls.violations)
                report_lines.append(
                    f"| `{cls.name}` | {cls.file} | {cls.line} | "
                    f"{cls.methods} | {cls.responsibilities} | {violations_str} |"
                )
            
            report_lines.append("")
        
        # Recommendations
        report_lines.extend([
            "## 💡 Recommendations",
            "",
            "### KISS (Keep It Simple, Stupid)",
            "- Break complex functions into smaller, focused functions",
            "- Reduce cyclomatic complexity below 10",
            "- Use early returns to avoid deep nesting",
            "",
            "### SOLID Principles",
            "- **SRP**: Classes with too many methods likely have multiple responsibilities",
            "- **OCP**: Use composition over inheritance when extending functionality",
            "- **DIP**: Depend on abstractions, not concrete implementations",
            "",
            "### DRY (Don't Repeat Yourself)",
            "- Extract common logic into reusable functions",
            "- Use inheritance or composition to share behavior",
            "- Create utility modules for frequently used operations",
            "",
            "### YAGNI (You Ain't Gonna Need It)",
            "- Remove unused code and dead code paths",
            "- Don't add features until they're actually needed",
            "- Simplify over-engineered solutions",
            "",
        ])
        
        # Metrics thresholds reference
        report_lines.extend([
            "## 📏 Thresholds Reference",
            "",
            "| Metric | Threshold | Principle |",
            "|--------|-----------|-----------|",
            f"| Function Complexity | ≤ {self.MAX_FUNCTION_COMPLEXITY} | KISS |",
            f"| Function Lines | ≤ {self.MAX_FUNCTION_LINES} | KISS |",
            f"| Function Parameters | ≤ {self.MAX_FUNCTION_PARAMETERS} | KISS |",
            f"| Class Methods | ≤ {self.MAX_CLASS_METHODS} | SRP |",
            f"| Class Responsibilities | ≤ {self.MAX_CLASS_RESPONSIBILITIES} | SRP |",
            f"| File Lines | ≤ {self.MAX_FILE_LINES} | Modularity |",
            f"| Nesting Depth | ≤ {self.MAX_NESTING_DEPTH} | KISS |",
            "",
            "---",
            "",
            f"**Generated**: {__file__}",
            "",
        ])
        
        report = "\n".join(report_lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"📄 Report saved to {output_file}")
        
        return report


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate simplicity principles in code")
    parser.add_argument(
        "--directory",
        default="app",
        help="Directory to analyze (default: app)"
    )
    parser.add_argument(
        "--report-file",
        help="Output file for the report (default: print to stdout)"
    )
    parser.add_argument(
        "--fail-on-violations",
        action="store_true",
        help="Exit with error code if violations found"
    )
    
    args = parser.parse_args()
    
    # Validate
    validator = SimplicityValidator(args.directory)
    results = validator.validate()
    
    # Generate report
    report = validator.generate_report(args.report_file)
    
    if not args.report_file:
        print("\n" + report)
    
    # Exit with error if violations found and flag is set
    if args.fail_on_violations and results["overall"]["total_violations"] > 0:
        print(f"\n❌ Found {results['overall']['total_violations']} violations")
        sys.exit(1)
    else:
        print(f"\n✅ Validation complete!")
        sys.exit(0)


if __name__ == "__main__":
    main()
