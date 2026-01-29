import ast
from datetime import datetime
from pathlib import Path

from app.core.logging import get_logger
from app.services.overmind.code_intelligence.analyzers.complexity import ComplexityAnalyzer
from app.services.overmind.code_intelligence.analyzers.git import GitAnalyzer
from app.services.overmind.code_intelligence.analyzers.hotspot import HotspotAnalyzer
from app.services.overmind.code_intelligence.analyzers.smells import StructuralSmellDetector
from app.services.overmind.code_intelligence.analyzers.statistics import StatisticsAnalyzer
from app.services.overmind.code_intelligence.models import (
    ComplexityStats,
    FileMetrics,
    LineStats,
    ProjectAnalysis,
    ProjectStats,
)

logger = get_logger(__name__)


class StructuralCodeIntelligence:
    """Main Structural Intelligence Analyzer"""

    def __init__(self, repo_path: Path, target_paths: list[str]):
        self.repo_path = repo_path
        self.target_paths = target_paths
        self.git_analyzer = GitAnalyzer(repo_path)
        self.smell_detector = StructuralSmellDetector()
        self.statistics_analyzer = StatisticsAnalyzer()
        self.hotspot_analyzer = HotspotAnalyzer()

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
        if file_path.suffix != ".py":
            return False

        # Must be in target paths
        return any(target in path_str for target in self.target_paths)

    def _create_base_metrics(
        self,
        file_path: Path,
        lines: list[str],
        analyzer: ComplexityAnalyzer,
        line_stats: LineStats,
        complexity_stats: ComplexityStats,
    ) -> FileMetrics:
        """
        Create base FileMetrics object.

        Args:
            file_path: Path to file
            lines: File lines
            analyzer: Complexity analyzer
            line_stats: Basic line statistics
            complexity_stats: Complexity statistics

        Returns:
            FileMetrics: Base metrics object
        """
        relative_path = str(file_path.relative_to(self.repo_path))

        return FileMetrics(
            file_path=str(file_path),
            relative_path=relative_path,
            total_lines=len(lines),
            code_lines=line_stats.code_lines,
            comment_lines=line_stats.comment_lines,
            blank_lines=line_stats.blank_lines,
            num_classes=len(analyzer.classes),
            num_functions=len(analyzer.functions),
            num_public_functions=sum(1 for f in analyzer.functions if f["is_public"]),
            file_complexity=analyzer.file_complexity,
            avg_function_complexity=round(complexity_stats.avg_complexity, 2),
            max_function_complexity=complexity_stats.max_complexity,
            max_function_name=complexity_stats.max_func_name,
            complexity_std_dev=round(complexity_stats.std_dev, 2),
            max_nesting_depth=analyzer.max_nesting,
            avg_nesting_depth=round(complexity_stats.avg_nesting, 2),
            num_imports=len(analyzer.imports),
            function_details=analyzer.functions,
        )

    def _enrich_with_git_metrics(self, metrics: FileMetrics) -> None:
        """
        Enrich metrics with Git information.

        Args:
            metrics: Metrics object to enrich
        """
        git_metrics = self.git_analyzer.analyze_file_history(metrics.relative_path)
        metrics.total_commits = git_metrics["total_commits"]
        metrics.commits_last_6months = git_metrics["commits_last_6months"]
        metrics.commits_last_12months = git_metrics["commits_last_12months"]
        metrics.num_authors = git_metrics["num_authors"]
        metrics.bugfix_commits = git_metrics["bugfix_commits"]
        metrics.branches_modified = git_metrics["branches_modified"]

    def _enrich_with_smells(self, metrics: FileMetrics, imports: list[dict]) -> None:
        """
        Enrich metrics with structural smells.

        Args:
            metrics: Metrics object to enrich
            imports: List of imports
        """
        smells = self.smell_detector.detect_smells(metrics.relative_path, metrics, imports)
        metrics.is_god_class = smells["is_god_class"]
        metrics.has_layer_mixing = smells["has_layer_mixing"]
        metrics.has_cross_layer_imports = smells["has_cross_layer_imports"]

    def analyze_file(self, file_path: Path) -> FileMetrics | None:
        """
        Analyze a single file.

        Args:
            file_path: Path to file

        Returns:
            FileMetrics or None
        """
        try:
            content, lines = self._read_file_content(file_path)

            # Calculate lines stats
            line_stats = self.statistics_analyzer.count_lines(lines)

            # Analyze AST
            tree = ast.parse(content)
            analyzer = ComplexityAnalyzer()
            analyzer.visit(tree)

            # Calculate complexity stats
            complexity_stats = self.statistics_analyzer.calculate_complexity_stats(
                analyzer.functions
            )

            # Create base metrics
            metrics = self._create_base_metrics(
                file_path,
                lines,
                analyzer,
                line_stats,
                complexity_stats,
            )

            # Enrich with Git metrics
            self._enrich_with_git_metrics(metrics)

            # Enrich with smells
            self._enrich_with_smells(metrics, analyzer.imports)

            return metrics

        except (OSError, UnicodeDecodeError, SyntaxError, ValueError) as exc:
            logger.warning("Failed to analyze file: %s due to %s", file_path, exc)
            return None

    def _read_file_content(self, file_path: Path) -> tuple[str, list[str]]:
        """
        Read file content and split into lines.

        Args:
            file_path: Path to file

        Returns:
            Tuple of content and lines
        """
        with open(file_path, encoding="utf-8") as file_handle:
            content = file_handle.read()
        return content, content.split("\n")

    def analyze_project(self) -> ProjectAnalysis:
        """
        Analyze entire project.

        Returns:
            ProjectAnalysis object
        """
        self._print_analysis_header()
        all_metrics = self._collect_file_metrics()

        # Calculate hotspots using the analyzer
        logger.info("📊 Calculating hotspot scores...")
        self.hotspot_analyzer.calculate_and_sort_hotspots(all_metrics)

        return self._build_project_analysis(all_metrics)

    def _print_analysis_header(self) -> None:
        """Print analysis header."""
        logger.info("🔍 Starting Structural Code Intelligence Analysis...")
        logger.info("📁 Repository: %s", self.repo_path)
        logger.info("🎯 Target paths: %s", ", ".join(self.target_paths))

    def _collect_file_metrics(self) -> list[FileMetrics]:
        """
        Collect metrics for all files.

        Returns:
            List of FileMetrics
        """
        all_metrics: list[FileMetrics] = []

        for target in self.target_paths:
            target_path = self.repo_path / target
            if not target_path.exists():
                logger.warning("⚠️  Path not found: %s", target_path)
                continue

            logger.info("📂 Analyzing %s...", target)
            self._analyze_target_path(target_path, all_metrics)

        logger.info("✅ Analyzed %s files", len(all_metrics))
        return all_metrics

    def _iter_python_files(self, target_path: Path) -> list[Path]:
        """
        Return list of Python files in target path.

        Args:
            target_path: Target path

        Returns:
            List of Python files
        """
        return list(target_path.rglob("*.py"))

    def _analyze_target_path(self, target_path: Path, all_metrics: list[FileMetrics]) -> None:
        """
        Analyze all files in a target path.

        Args:
            target_path: Target path
            all_metrics: List to append metrics to
        """
        for py_file in self._iter_python_files(target_path):
            if self.should_analyze(py_file):
                metrics = self.analyze_file(py_file)
                if metrics:
                    all_metrics.append(metrics)
                    logger.info("  ✓ %s", metrics.relative_path)

    def _build_project_analysis(self, all_metrics: list[FileMetrics]) -> ProjectAnalysis:
        """
        Build final project analysis.

        Args:
            all_metrics: List of metrics

        Returns:
            ProjectAnalysis
        """
        stats = self._calculate_project_statistics(all_metrics)
        hotspots = self.hotspot_analyzer.identify_hotspots(all_metrics)

        return ProjectAnalysis(
            timestamp=datetime.now().isoformat(),
            total_files=len(all_metrics),
            total_lines=stats.total_lines,
            total_code_lines=stats.total_code,
            total_functions=stats.total_functions,
            total_classes=stats.total_classes,
            avg_file_complexity=stats.avg_complexity,
            max_file_complexity=stats.max_complexity,
            critical_hotspots=hotspots.critical,
            high_hotspots=hotspots.high,
            files=all_metrics,
        )

    def _calculate_project_statistics(self, all_metrics: list[FileMetrics]) -> ProjectStats:
        """
        Calculate overall project statistics.

        Args:
            all_metrics: List of metrics

        Returns:
            ProjectStats
        """
        avg_complexity = self._calculate_average_complexity(all_metrics)
        return ProjectStats(
            total_lines=sum(m.total_lines for m in all_metrics),
            total_code=sum(m.code_lines for m in all_metrics),
            total_functions=sum(m.num_functions for m in all_metrics),
            total_classes=sum(m.num_classes for m in all_metrics),
            avg_complexity=round(avg_complexity, 2),
            max_complexity=max((m.file_complexity for m in all_metrics), default=0),
        )

    def _calculate_average_complexity(self, all_metrics: list[FileMetrics]) -> float:
        """
        Calculate average complexity across all files.

        Args:
            all_metrics: List of metrics

        Returns:
            Average complexity
        """
        if not all_metrics:
            return 0.0
        return sum(m.file_complexity for m in all_metrics) / len(all_metrics)
