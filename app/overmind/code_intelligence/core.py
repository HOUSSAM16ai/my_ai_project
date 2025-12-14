import ast
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .models import FileMetrics, ProjectAnalysis
from .analyzers.git import GitAnalyzer
from .analyzers.smells import StructuralSmellDetector
from .analyzers.complexity import ComplexityAnalyzer


class StructuralCodeIntelligence:
    """Main Structural Intelligence Analyzer"""

    def __init__(self, repo_path: Path, target_paths: List[str]):
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
        """Should this file be analyzed?"""
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

    def analyze_file(self, file_path: Path) -> Optional[FileMetrics]:
        """Comprehensive single file analysis"""
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
            # print(f"Error analyzing {file_path}: {e}", file=sys.stderr)
            return None

    def calculate_hotspot_scores(self, all_metrics: List[FileMetrics]) -> None:
        """Calculate hotspot scores with normalization"""
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
        def normalize(values: List[float]) -> List[float]:
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
        """Analyze entire project"""
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
