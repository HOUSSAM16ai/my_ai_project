#!/usr/bin/env python3
"""
المرحلة الأولى: التحليل الكمي البنيوي لقاعدة الشيفرة
Structural Code Intelligence Pass - Phase 1

نظام تحليل متقدم فائق الجودة لقياس صحة الكود وتحديد مناطق الخطر (Hotspots)
بمعايير صرامة فائقة الاحترافية

Features:
- Cyclomatic Complexity Analysis (McCabe)
- Code Size Metrics (LOC, Classes, Functions)
- Git History Analysis (Commits, Authors, Bugfixes)
- Structural Smell Detection (God Classes, Layer Mixing, Cross-Layer Imports)
- Hotspot Scoring with Weighted Ranking
- Multiple Output Formats (JSON, CSV, HTML Heatmap, Markdown)
- Reproducible Baseline for Future Comparisons

Author: Houssam Benmerah
Version: 1.0.0
Date: 2025-12-10
"""

import ast
import csv
import json
import os
import subprocess
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class FileMetrics:
    """مقاييس شاملة لملف واحد - Comprehensive metrics for a single file"""

    # معلومات أساسية - Basic Information
    file_path: str
    relative_path: str

    # مقاييس الحجم - Size Metrics
    total_lines: int = 0
    code_lines: int = 0  # Lines of Code (LOC) excluding comments and blanks
    comment_lines: int = 0
    blank_lines: int = 0
    num_classes: int = 0
    num_functions: int = 0
    num_public_functions: int = 0

    # مقاييس التعقيد - Complexity Metrics
    file_complexity: int = 0  # Total cyclomatic complexity
    avg_function_complexity: float = 0.0
    max_function_complexity: int = 0
    max_function_name: str = ""
    complexity_std_dev: float = 0.0

    # مقاييس التعشيش - Nesting Metrics
    max_nesting_depth: int = 0
    avg_nesting_depth: float = 0.0

    # ديناميكية التغيير - Change Volatility
    total_commits: int = 0
    commits_last_6months: int = 0
    commits_last_12months: int = 0
    num_authors: int = 0
    bugfix_commits: int = 0
    branches_modified: int = 0

    # الروائح البنيوية - Structural Smells
    is_god_class: bool = False
    has_layer_mixing: bool = False
    has_cross_layer_imports: bool = False
    num_imports: int = 0
    num_external_dependencies: int = 0

    # تفاصيل الدوال - Function Details
    function_details: list[dict[str, Any]] = field(default_factory=list)

    # درجات الخطورة - Hotspot Scores
    complexity_rank: float = 0.0
    volatility_rank: float = 0.0
    smell_rank: float = 0.0
    hotspot_score: float = 0.0
    priority_tier: str = ""  # "CRITICAL", "HIGH", "MEDIUM", "LOW"


@dataclass
class ProjectAnalysis:
    """تحليل شامل للمشروع - Comprehensive project analysis"""

    timestamp: str
    total_files: int
    total_lines: int
    total_code_lines: int
    total_functions: int
    total_classes: int
    avg_file_complexity: float
    max_file_complexity: int

    # Hotspots
    critical_hotspots: list[str] = field(default_factory=list)  # Top 20
    high_hotspots: list[str] = field(default_factory=list)  # Next 20

    files: list[FileMetrics] = field(default_factory=list)


class ComplexityAnalyzer(ast.NodeVisitor):
    """محلل التعقيد السيكلوماتيكي المتقدم - Advanced Cyclomatic Complexity Analyzer"""

    def __init__(self):
        self.file_complexity = 0
        self.functions = []
        self.classes = []
        self.current_class = None
        self.imports = []
        self.max_nesting = 0

    def visit_ClassDef(self, node: ast.ClassDef):
        """تحليل الكلاسات - Analyze classes"""
        self.current_class = node.name
        self.classes.append(
            {
                "name": node.name,
                "line": node.lineno,
                "methods": [],
                "loc": self._count_node_lines(node)
            }
        )
        self.generic_visit(node)
        self.current_class = None

    def visit_FunctionDef(self, node: ast.FunctionDef):
        """تحليل الدوال - Analyze functions"""
        complexity = self._calculate_complexity(node)
        nesting = self._calculate_nesting(node)
        loc = self._count_node_lines(node)

        func_info = {
            "name": node.name,
            "line": node.lineno,
            "complexity": complexity,
            "nesting_depth": nesting,
            "loc": loc,
            "is_public": not node.name.startswith("_"),
            "class": self.current_class,
            "num_parameters": len(node.args.args),
        }

        self.functions.append(func_info)
        self.file_complexity += complexity
        self.max_nesting = max(self.max_nesting, nesting)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        """تحليل الدوال غير المتزامنة - Analyze async functions"""
        self.visit_FunctionDef(node)

    def visit_Import(self, node: ast.Import):
        """تتبع الاستيرادات - Track imports"""
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        """تتبع استيرادات from - Track from imports"""
        if node.module:
            self.imports.append(node.module)
        self.generic_visit(node)

    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """حساب التعقيد السيكلوماتيكي (McCabe) - Calculate McCabe Cyclomatic Complexity"""
        complexity = 1  # Base complexity

        for child in ast.walk(node):
            # Decision points
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, (ast.With, ast.AsyncWith)):
                complexity += 1
            # Boolean operators
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            # Comprehensions
            elif isinstance(child, (ast.ListComp, ast.DictComp, ast.SetComp, ast.GeneratorExp)):
                complexity += 1

        return complexity

    def _calculate_nesting(self, node: ast.FunctionDef) -> int:
        """حساب عمق التعشيش الأقصى - Calculate maximum nesting depth"""
        max_depth = 0

        def visit_node(n, depth):
            nonlocal max_depth
            max_depth = max(max_depth, depth)

            for child in ast.iter_child_nodes(n):
                if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor, ast.Try, ast.With)):
                    visit_node(child, depth + 1)
                else:
                    visit_node(child, depth)

        visit_node(node, 0)
        return max_depth

    def _count_node_lines(self, node) -> int:
        """حساب عدد أسطر العقدة - Count node lines"""
        if hasattr(node, "end_lineno") and node.end_lineno:
            return node.end_lineno - node.lineno + 1
        return 1


class GitAnalyzer:
    """محلل تاريخ Git - Git History Analyzer"""

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path

    def analyze_file_history(self, file_path: str) -> dict[str, Any]:
        """تحليل تاريخ التعديلات على ملف - Analyze file modification history"""
        try:
            # Total commits
            result = subprocess.run(
                ["git", "log", "--follow", "--oneline", "--", file_path],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            total_commits = len(result.stdout.strip().split("\n")) if result.stdout.strip() else 0

            # Commits in last 6 months
            result_6m = subprocess.run(
                ["git", "log", "--follow", "--since=6 months ago", "--oneline", "--", file_path],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            commits_6m = len(result_6m.stdout.strip().split("\n")) if result_6m.stdout.strip() else 0

            # Commits in last 12 months
            result_12m = subprocess.run(
                ["git", "log", "--follow", "--since=12 months ago", "--oneline", "--", file_path],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            commits_12m = len(result_12m.stdout.strip().split("\n")) if result_12m.stdout.strip() else 0

            # Authors
            result_authors = subprocess.run(
                ["git", "log", "--follow", "--format=%an", "--", file_path],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            authors = set(result_authors.stdout.strip().split("\n")) if result_authors.stdout.strip() else set()
            num_authors = len(authors)

            # Bugfix commits
            result_bugfix = subprocess.run(
                [
                    "git",
                    "log",
                    "--follow",
                    "--oneline",
                    "--grep=fix",
                    "--grep=bug",
                    "--grep=hotfix",
                    "-i",
                    "--",
                    file_path,
                ],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            bugfix_commits = len(result_bugfix.stdout.strip().split("\n")) if result_bugfix.stdout.strip() else 0

            # Branches (approximate - get unique branch names)
            result_branches = subprocess.run(
                ["git", "log", "--follow", "--all", "--format=%D", "--", file_path],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            branches = set()
            if result_branches.stdout.strip():
                for line in result_branches.stdout.strip().split("\n"):
                    if line:
                        # Extract branch names from "HEAD -> main, origin/main" format
                        parts = [p.strip() for p in line.split(",")]
                        for part in parts:
                            if "origin/" in part or "->" in part:
                                continue
                            if part and not part.startswith("tag:"):
                                branches.add(part)

            return {
                "total_commits": total_commits,
                "commits_last_6months": commits_6m,
                "commits_last_12months": commits_12m,
                "num_authors": num_authors,
                "bugfix_commits": bugfix_commits,
                "branches_modified": len(branches),
            }

        except Exception as e:
            print(f"Warning: Git analysis failed for {file_path}: {e}", file=sys.stderr)
            return {
                "total_commits": 0,
                "commits_last_6months": 0,
                "commits_last_12months": 0,
                "num_authors": 0,
                "bugfix_commits": 0,
                "branches_modified": 0,
            }


class StructuralSmellDetector:
    """كاشف الروائح البنيوية - Structural Smell Detector"""

    # God class thresholds
    GOD_CLASS_LOC_THRESHOLD = 500
    GOD_CLASS_METHODS_THRESHOLD = 20

    # Layer mixing patterns
    LAYER_PATTERNS = {
        "api": ["api", "routers", "endpoints", "controllers"],
        "service": ["services", "use_cases", "application"],
        "infrastructure": ["infrastructure", "repositories", "adapters"],
        "domain": ["domain", "models", "entities"],
    }

    def detect_smells(self, file_path: str, metrics: FileMetrics, imports: list[str]) -> dict[str, bool]:
        """كشف الروائح البنيوية - Detect structural smells"""
        smells = {
            "is_god_class": False,
            "has_layer_mixing": False,
            "has_cross_layer_imports": False,
        }

        # God class detection
        if metrics.num_classes > 0:
            if metrics.code_lines > self.GOD_CLASS_LOC_THRESHOLD:
                smells["is_god_class"] = True
            elif metrics.num_functions > self.GOD_CLASS_METHODS_THRESHOLD:
                smells["is_god_class"] = True

        # Detect current file layer
        current_layer = self._detect_layer(file_path)

        # Check for layer mixing in imports
        if current_layer:
            import_layers = set()
            for imp in imports:
                imp_layer = self._detect_layer(imp)
                if imp_layer and imp_layer != current_layer:
                    import_layers.add(imp_layer)

            # Cross-layer imports (e.g., service importing from api)
            if import_layers:
                smells["has_cross_layer_imports"] = True

                # Layer mixing (multiple responsibilities)
                if len(import_layers) > 1:
                    smells["has_layer_mixing"] = True

        return smells

    def _detect_layer(self, path: str) -> str | None:
        """تحديد الطبقة المعمارية من المسار - Detect architectural layer from path"""
        path_lower = path.lower()
        for layer, patterns in self.LAYER_PATTERNS.items():
            if any(pattern in path_lower for pattern in patterns):
                return layer
        return None


class StructuralCodeIntelligence:
    """المحلل الرئيسي للذكاء البنيوي - Main Structural Intelligence Analyzer"""

    def __init__(self, repo_path: Path, target_paths: list[str]):
        self.repo_path = repo_path
        self.target_paths = target_paths
        self.git_analyzer = GitAnalyzer(repo_path)
        self.smell_detector = StructuralSmellDetector()

        # Exclusion patterns
        self.exclude_patterns = [
            "__pycache__",
            ".pyc",
            "venv",
            "site-packages",
            "migrations",
            ".git",
            "sandbox",
            "playground",
            "experiments",
            "test_",
            "_test.py",
        ]

    def should_analyze(self, file_path: Path) -> bool:
        """هل يجب تحليل هذا الملف؟ - Should this file be analyzed?"""
        path_str = str(file_path)

        # Check exclusions
        for pattern in self.exclude_patterns:
            if pattern in path_str:
                return False

        # Must be Python file
        if not file_path.suffix == ".py":
            return False

        # Must be in target paths
        for target in self.target_paths:
            if target in path_str:
                return True

        return False

    def analyze_file(self, file_path: Path) -> FileMetrics | None:
        """تحليل ملف واحد بشكل شامل - Comprehensive single file analysis"""
        try:
            # Read file
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            # Count lines
            code_lines = 0
            comment_lines = 0
            blank_lines = 0

            for line in lines:
                stripped = line.strip()
                if not stripped:
                    blank_lines += 1
                elif stripped.startswith("#"):
                    comment_lines += 1
                else:
                    code_lines += 1

            # Parse AST
            tree = ast.parse(content)
            analyzer = ComplexityAnalyzer()
            analyzer.visit(tree)

            # Calculate statistics
            function_complexities = [f["complexity"] for f in analyzer.functions]
            avg_complexity = sum(function_complexities) / len(function_complexities) if function_complexities else 0
            max_complexity = max(function_complexities) if function_complexities else 0
            max_func_name = ""
            if max_complexity > 0:
                for f in analyzer.functions:
                    if f["complexity"] == max_complexity:
                        max_func_name = f["name"]
                        break

            # Standard deviation
            if len(function_complexities) > 1:
                mean = avg_complexity
                variance = sum((x - mean) ** 2 for x in function_complexities) / len(function_complexities)
                std_dev = variance**0.5
            else:
                std_dev = 0.0

            # Nesting statistics
            nesting_depths = [f["nesting_depth"] for f in analyzer.functions]
            avg_nesting = sum(nesting_depths) / len(nesting_depths) if nesting_depths else 0

            # Create metrics object
            relative_path = str(file_path.relative_to(self.repo_path))
            metrics = FileMetrics(
                file_path=str(file_path),
                relative_path=relative_path,
                total_lines=len(lines),
                code_lines=code_lines,
                comment_lines=comment_lines,
                blank_lines=blank_lines,
                num_classes=len(analyzer.classes),
                num_functions=len(analyzer.functions),
                num_public_functions=sum(1 for f in analyzer.functions if f["is_public"]),
                file_complexity=analyzer.file_complexity,
                avg_function_complexity=round(avg_complexity, 2),
                max_function_complexity=max_complexity,
                max_function_name=max_func_name,
                complexity_std_dev=round(std_dev, 2),
                max_nesting_depth=analyzer.max_nesting,
                avg_nesting_depth=round(avg_nesting, 2),
                num_imports=len(analyzer.imports),
                function_details=analyzer.functions,
            )

            # Git analysis
            git_metrics = self.git_analyzer.analyze_file_history(relative_path)
            metrics.total_commits = git_metrics["total_commits"]
            metrics.commits_last_6months = git_metrics["commits_last_6months"]
            metrics.commits_last_12months = git_metrics["commits_last_12months"]
            metrics.num_authors = git_metrics["num_authors"]
            metrics.bugfix_commits = git_metrics["bugfix_commits"]
            metrics.branches_modified = git_metrics["branches_modified"]

            # Structural smells
            smells = self.smell_detector.detect_smells(relative_path, metrics, analyzer.imports)
            metrics.is_god_class = smells["is_god_class"]
            metrics.has_layer_mixing = smells["has_layer_mixing"]
            metrics.has_cross_layer_imports = smells["has_cross_layer_imports"]

            return metrics

        except Exception as e:
            print(f"Error analyzing {file_path}: {e}", file=sys.stderr)
            return None

    def calculate_hotspot_scores(self, all_metrics: list[FileMetrics]) -> None:
        """حساب درجات الخطورة مع التطبيع - Calculate hotspot scores with normalization"""
        if not all_metrics:
            return

        # Extract values for normalization
        complexities = [m.file_complexity for m in all_metrics]
        volatilities = [m.commits_last_12months for m in all_metrics]
        smells = [
            (1 if m.is_god_class else 0) + (1 if m.has_layer_mixing else 0) + (1 if m.has_cross_layer_imports else 0)
            for m in all_metrics
        ]

        # Normalize to 0-1 range
        def normalize(values: list[float]) -> list[float]:
            if not values or max(values) == 0:
                return [0.0] * len(values)
            max_val = max(values)
            return [v / max_val for v in values]

        complexity_ranks = normalize(complexities)
        volatility_ranks = normalize(volatilities)
        smell_ranks = normalize(smells)

        # Calculate weighted hotspot scores
        # Score = 0.4 × Complexity + 0.4 × Volatility + 0.2 × Smells
        w1, w2, w3 = 0.4, 0.4, 0.2

        for i, metrics in enumerate(all_metrics):
            metrics.complexity_rank = round(complexity_ranks[i], 4)
            metrics.volatility_rank = round(volatility_ranks[i], 4)
            metrics.smell_rank = round(smell_ranks[i], 4)

            score = w1 * complexity_ranks[i] + w2 * volatility_ranks[i] + w3 * smell_ranks[i]
            metrics.hotspot_score = round(score, 4)

            # Assign priority tier
            if score >= 0.7:
                metrics.priority_tier = "CRITICAL"
            elif score >= 0.5:
                metrics.priority_tier = "HIGH"
            elif score >= 0.3:
                metrics.priority_tier = "MEDIUM"
            else:
                metrics.priority_tier = "LOW"

    def analyze_project(self) -> ProjectAnalysis:
        """تحليل المشروع بالكامل - Analyze entire project"""
        print("🔍 Starting Structural Code Intelligence Analysis...")
        print(f"📁 Repository: {self.repo_path}")
        print(f"🎯 Target paths: {', '.join(self.target_paths)}")
        print()

        all_metrics = []

        # Find and analyze all files
        for target in self.target_paths:
            target_path = self.repo_path / target
            if not target_path.exists():
                print(f"⚠️  Path not found: {target_path}")
                continue

            print(f"📂 Analyzing {target}...")
            py_files = list(target_path.rglob("*.py"))
            for py_file in py_files:
                if self.should_analyze(py_file):
                    metrics = self.analyze_file(py_file)
                    if metrics:
                        all_metrics.append(metrics)
                        print(f"  ✓ {metrics.relative_path}")

        print(f"\n✅ Analyzed {len(all_metrics)} files")

        # Calculate hotspot scores
        print("\n📊 Calculating hotspot scores...")
        self.calculate_hotspot_scores(all_metrics)

        # Sort by hotspot score
        all_metrics.sort(key=lambda m: m.hotspot_score, reverse=True)

        # Calculate project statistics
        total_lines = sum(m.total_lines for m in all_metrics)
        total_code = sum(m.code_lines for m in all_metrics)
        total_functions = sum(m.num_functions for m in all_metrics)
        total_classes = sum(m.num_classes for m in all_metrics)
        avg_complexity = (
            sum(m.file_complexity for m in all_metrics) / len(all_metrics) if all_metrics else 0
        )
        max_complexity = max((m.file_complexity for m in all_metrics), default=0)

        # Identify hotspots
        critical_hotspots = [m.relative_path for m in all_metrics[:20]]
        high_hotspots = [m.relative_path for m in all_metrics[20:40]]

        analysis = ProjectAnalysis(
            timestamp=datetime.now().isoformat(),
            total_files=len(all_metrics),
            total_lines=total_lines,
            total_code_lines=total_code,
            total_functions=total_functions,
            total_classes=total_classes,
            avg_file_complexity=round(avg_complexity, 2),
            max_file_complexity=max_complexity,
            critical_hotspots=critical_hotspots,
            high_hotspots=high_hotspots,
            files=all_metrics,
        )

        return analysis


def save_json_report(analysis: ProjectAnalysis, output_path: Path) -> None:
    """حفظ التقرير بصيغة JSON - Save report as JSON"""
    data = asdict(analysis)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"💾 JSON report saved: {output_path}")


def save_csv_report(analysis: ProjectAnalysis, output_path: Path) -> None:
    """حفظ التقرير بصيغة CSV - Save report as CSV"""
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        if not analysis.files:
            return

        fieldnames = [
            "relative_path",
            "code_lines",
            "num_classes",
            "num_functions",
            "file_complexity",
            "avg_function_complexity",
            "max_function_complexity",
            "commits_last_12months",
            "bugfix_commits",
            "is_god_class",
            "has_layer_mixing",
            "has_cross_layer_imports",
            "hotspot_score",
            "priority_tier",
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for file_metrics in analysis.files:
            row = {k: getattr(file_metrics, k) for k in fieldnames}
            writer.writerow(row)

    print(f"💾 CSV report saved: {output_path}")


def generate_heatmap_html(analysis: ProjectAnalysis, output_path: Path) -> None:
    """توليد خريطة حرارية بصيغة HTML - Generate HTML heatmap"""
    
    # Build file rows HTML
    file_rows_html = []
    for file_metrics in analysis.files[:50]:  # Top 50 files
        tier_class = file_metrics.priority_tier.lower()
        smells = []
        if file_metrics.is_god_class:
            smells.append("God Class")
        if file_metrics.has_layer_mixing:
            smells.append("Layer Mixing")
        if file_metrics.has_cross_layer_imports:
            smells.append("Cross-Layer Imports")

        smells_html = ", ".join(smells) if smells else "لا توجد"

        row_html = f"""
            <div class="file-row {tier_class}">
                <div class="file-name">
                    <span class="badge {tier_class}">{file_metrics.priority_tier}</span>
                    {file_metrics.relative_path}
                </div>
                <div class="file-metrics">
                    <div class="metric">
                        <span class="metric-label">درجة الخطورة:</span>
                        <span class="metric-value">{file_metrics.hotspot_score:.4f}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">التعقيد الكلي:</span>
                        <span class="metric-value">{file_metrics.file_complexity}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">أسطر الكود:</span>
                        <span class="metric-value">{file_metrics.code_lines}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">الدوال:</span>
                        <span class="metric-value">{file_metrics.num_functions}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">التعديلات (12 شهر):</span>
                        <span class="metric-value">{file_metrics.commits_last_12months}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">إصلاحات الأخطاء:</span>
                        <span class="metric-value">{file_metrics.bugfix_commits}</span>
                    </div>
                    <div class="metric">
                        <span class="metric-label">الروائح البنيوية:</span>
                        <span class="metric-value">{smells_html}</span>
                    </div>
                </div>
            </div>"""
        file_rows_html.append(row_html)

    html_content = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>خريطة حرارية - التحليل البنيوي للكود</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #1a1a1a;
            color: #e0e0e0;
            padding: 20px;
            direction: rtl;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        h1 {{
            color: #00d4ff;
            text-align: center;
            margin-bottom: 10px;
        }}
        .summary {{
            background: #2a2a2a;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 30px;
            border-left: 4px solid #00d4ff;
        }}
        .summary h2 {{
            margin-top: 0;
            color: #00d4ff;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 15px;
        }}
        .stat {{
            background: #1a1a1a;
            padding: 15px;
            border-radius: 6px;
        }}
        .stat-label {{
            color: #888;
            font-size: 0.9em;
            margin-bottom: 5px;
        }}
        .stat-value {{
            font-size: 1.5em;
            font-weight: bold;
            color: #00d4ff;
        }}
        .heatmap {{
            display: grid;
            gap: 10px;
        }}
        .file-row {{
            background: #2a2a2a;
            padding: 15px;
            border-radius: 6px;
            border-right: 6px solid;
            transition: transform 0.2s;
        }}
        .file-row:hover {{
            transform: translateX(-5px);
            box-shadow: 0 4px 12px rgba(0, 212, 255, 0.3);
        }}
        .file-row.critical {{
            border-right-color: #ff4444;
            background: linear-gradient(90deg, #2a2a2a 0%, #3a1a1a 100%);
        }}
        .file-row.high {{
            border-right-color: #ff9944;
            background: linear-gradient(90deg, #2a2a2a 0%, #3a2a1a 100%);
        }}
        .file-row.medium {{
            border-right-color: #ffdd44;
            background: linear-gradient(90deg, #2a2a2a 0%, #3a3a1a 100%);
        }}
        .file-row.low {{
            border-right-color: #44ff44;
            background: linear-gradient(90deg, #2a2a2a 0%, #1a3a1a 100%);
        }}
        .file-name {{
            font-size: 1.1em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #fff;
        }}
        .file-metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            font-size: 0.9em;
        }}
        .metric {{
            display: flex;
            justify-content: space-between;
        }}
        .metric-label {{
            color: #888;
        }}
        .metric-value {{
            color: #00d4ff;
            font-weight: bold;
        }}
        .badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.85em;
            font-weight: bold;
            margin-right: 8px;
        }}
        .badge.critical {{
            background: #ff4444;
            color: white;
        }}
        .badge.high {{
            background: #ff9944;
            color: white;
        }}
        .badge.medium {{
            background: #ffdd44;
            color: black;
        }}
        .badge.low {{
            background: #44ff44;
            color: black;
        }}
        .legend {{
            background: #2a2a2a;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }}
        .legend-items {{
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
            margin-top: 10px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .legend-color {{
            width: 30px;
            height: 20px;
            border-radius: 4px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🔥 خريطة حرارية - التحليل البنيوي للكود</h1>
        <p style="text-align: center; color: #888;">تم الإنشاء: {analysis.timestamp}</p>
        
        <div class="summary">
            <h2>📊 ملخص المشروع</h2>
            <div class="stats">
                <div class="stat">
                    <div class="stat-label">إجمالي الملفات</div>
                    <div class="stat-value">{analysis.total_files}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">أسطر الكود</div>
                    <div class="stat-value">{analysis.total_code_lines:,}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">إجمالي الدوال</div>
                    <div class="stat-value">{analysis.total_functions}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">إجمالي الكلاسات</div>
                    <div class="stat-value">{analysis.total_classes}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">متوسط التعقيد</div>
                    <div class="stat-value">{analysis.avg_file_complexity:.1f}</div>
                </div>
                <div class="stat">
                    <div class="stat-label">أقصى تعقيد</div>
                    <div class="stat-value">{analysis.max_file_complexity}</div>
                </div>
            </div>
        </div>

        <div class="legend">
            <h3>دليل الألوان</h3>
            <div class="legend-items">
                <div class="legend-item">
                    <div class="legend-color" style="background: #ff4444;"></div>
                    <span>حرج (≥0.7)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ff9944;"></div>
                    <span>عالي (≥0.5)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ffdd44;"></div>
                    <span>متوسط (≥0.3)</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #44ff44;"></div>
                    <span>منخفض (&lt;0.3)</span>
                </div>
            </div>
        </div>

        <div class="heatmap">
            {"".join(file_rows_html)}
        </div>
    </div>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"💾 Heatmap HTML saved: {output_path}")


def generate_markdown_report(analysis: ProjectAnalysis, output_path: Path) -> None:
    """توليد تقرير بصيغة Markdown - Generate Markdown report"""
    md = f"""# 🔍 تقرير التحليل البنيوي للكود
**Phase 1: Structural Code Intelligence Analysis**

تم الإنشاء: {analysis.timestamp}

---

## 📊 ملخص المشروع

| المقياس | القيمة |
|---------|--------|
| إجمالي الملفات المحللة | {analysis.total_files} |
| إجمالي الأسطر | {analysis.total_lines:,} |
| أسطر الكود (LOC) | {analysis.total_code_lines:,} |
| إجمالي الدوال | {analysis.total_functions} |
| إجمالي الكلاسات | {analysis.total_classes} |
| متوسط التعقيد للملف | {analysis.avg_file_complexity:.2f} |
| أقصى تعقيد للملف | {analysis.max_file_complexity} |

---

## 🔥 Hotspots حرجة (Top 20)

الملفات التي تحتاج إلى معالجة فورية:

"""

    for i, path in enumerate(analysis.critical_hotspots, 1):
        # Find the file metrics
        file_m = next((f for f in analysis.files if f.relative_path == path), None)
        if file_m:
            md += f"{i}. **{path}**\n"
            md += f"   - درجة الخطورة: `{file_m.hotspot_score:.4f}` | "
            md += f"التعقيد: `{file_m.file_complexity}` | "
            md += f"التعديلات: `{file_m.commits_last_12months}` | "
            md += f"الأولوية: `{file_m.priority_tier}`\n\n"

    md += "\n---\n\n## ⚠️ Hotspots عالية (التالي 20)\n\n"

    for i, path in enumerate(analysis.high_hotspots, 1):
        file_m = next((f for f in analysis.files if f.relative_path == path), None)
        if file_m:
            md += f"{i}. **{path}** - درجة: `{file_m.hotspot_score:.4f}`\n"

    md += "\n---\n\n## 📈 توزيع الأولويات\n\n"

    # Count by priority
    priority_counts = defaultdict(int)
    for f in analysis.files:
        priority_counts[f.priority_tier] += 1

    md += f"- 🔴 حرجة (CRITICAL): {priority_counts['CRITICAL']}\n"
    md += f"- 🟠 عالية (HIGH): {priority_counts['HIGH']}\n"
    md += f"- 🟡 متوسطة (MEDIUM): {priority_counts['MEDIUM']}\n"
    md += f"- 🟢 منخفضة (LOW): {priority_counts['LOW']}\n"

    md += "\n---\n\n## 🦨 الروائح البنيوية المكتشفة\n\n"

    god_classes = [f for f in analysis.files if f.is_god_class]
    layer_mixing = [f for f in analysis.files if f.has_layer_mixing]
    cross_layer = [f for f in analysis.files if f.has_cross_layer_imports]

    md += f"- **God Classes**: {len(god_classes)} ملف\n"
    md += f"- **Layer Mixing**: {len(layer_mixing)} ملف\n"
    md += f"- **Cross-Layer Imports**: {len(cross_layer)} ملف\n"

    md += "\n---\n\n## 📋 الخطوات التالية\n\n"
    md += "بناءً على هذا التحليل، يُوصى بالبدء في معالجة الملفات الحرجة أولاً:\n\n"
    md += "1. تطبيق مبدأ المسؤولية الواحدة (SRP) على God Classes\n"
    md += "2. إعادة التقسيم الطبقي للملفات ذات Layer Mixing\n"
    md += "3. عكس التبعيات غير الصحيحة (Cross-Layer Imports)\n"
    md += "4. تبسيط الدوال عالية التعقيد\n"
    md += "5. تحسين الملفات الأكثر تعديلاً لتقليل الأخطاء المستقبلية\n"

    md += "\n---\n\n## 📝 ملاحظات\n\n"
    md += "- هذا التقرير يمثل baseline للمشروع الحالي\n"
    md += "- يجب استخدامه كمرجع لقياس التحسينات بعد تطبيق SOLID\n"
    md += "- جميع المقاييس قابلة لإعادة الإنتاج من خلال تشغيل الأداة مرة أخرى\n"
    md += "- التركيز على الملفات الحرجة سيحقق أكبر تأثير إيجابي\n"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md)

    print(f"💾 Markdown report saved: {output_path}")


def main():
    """النقطة الرئيسية لتشغيل التحليل - Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="المرحلة الأولى: التحليل الكمي البنيوي لقاعدة الشيفرة",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--repo-path",
        type=Path,
        default=Path.cwd(),
        help="مسار المشروع (افتراضي: المجلد الحالي)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("reports/structural_analysis"),
        help="مجلد حفظ التقارير",
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        default=["app/api", "app/services", "app/infrastructure", "app/application/use_cases"],
        help="المسارات المستهدفة للتحليل",
    )

    args = parser.parse_args()

    # Create output directory
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Run analysis
    analyzer = StructuralCodeIntelligence(args.repo_path, args.targets)
    analysis = analyzer.analyze_project()

    # Generate reports
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("\n📝 Generating reports...")
    save_json_report(analysis, args.output_dir / f"structural_analysis_{timestamp}.json")
    save_csv_report(analysis, args.output_dir / f"structural_analysis_{timestamp}.csv")
    generate_heatmap_html(analysis, args.output_dir / f"heatmap_{timestamp}.html")
    generate_markdown_report(analysis, args.output_dir / f"report_{timestamp}.md")

    # Also save as latest
    save_json_report(analysis, args.output_dir / "structural_analysis_latest.json")
    save_csv_report(analysis, args.output_dir / "structural_analysis_latest.csv")
    generate_heatmap_html(analysis, args.output_dir / "heatmap_latest.html")
    generate_markdown_report(analysis, args.output_dir / "report_latest.md")

    print("\n✅ Analysis complete!")
    print(f"\n📊 Summary:")
    print(f"  - Files analyzed: {analysis.total_files}")
    print(f"  - Critical hotspots: {len(analysis.critical_hotspots)}")
    print(f"  - High hotspots: {len(analysis.high_hotspots)}")
    print(f"\n📁 Reports saved to: {args.output_dir}")


if __name__ == "__main__":
    main()
