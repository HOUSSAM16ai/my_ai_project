import ast
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from app.core.logging import get_logger

from .analyzers.complexity import ComplexityAnalyzer
from .analyzers.git import GitAnalyzer
from .analyzers.smells import StructuralSmellDetector
from .models import FileMetrics, ProjectAnalysis

logger = get_logger(__name__)


@dataclass(frozen=True)
class _LineStats:
    """يمثل إحصائيات الأسطر الأساسية لملف واحد."""

    code_lines: int
    comment_lines: int
    blank_lines: int


@dataclass(frozen=True)
class _ComplexityStats:
    """يحمل إحصائيات التعقيد والتداخل بشكل موحد."""

    avg_complexity: float
    max_complexity: int
    max_func_name: str
    std_dev: float
    avg_nesting: float


@dataclass(frozen=True)
class _HotspotWeights:
    """يمثل أوزان حساب النقاط الساخنة."""

    complexity: float
    volatility: float
    smell: float


@dataclass(frozen=True)
class _HotspotConfig:
    """يمثل الإعدادات الثابتة لحساب النقاط الساخنة."""

    weights: _HotspotWeights


@dataclass(frozen=True)
class _NormalizedRanks:
    """يحمل القيم المطبعة الخاصة بحساب النقاط الساخنة."""

    complexity: list[float]
    volatility: list[float]
    smell: list[float]


@dataclass(frozen=True)
class _ProjectStats:
    """يمثل إحصائيات المشروع الإجمالية."""

    total_lines: int
    total_code: int
    total_functions: int
    total_classes: int
    avg_complexity: float
    max_complexity: int


@dataclass(frozen=True)
class _HotspotBuckets:
    """يحمل قوائم النقاط الساخنة حسب الأولوية."""

    critical: list[str]
    high: list[str]


class StructuralCodeIntelligence:
    """Main Structural Intelligence Analyzer"""

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

    def _count_lines(self, lines: list[str]) -> _LineStats:
        """
        حساب أنواع الأسطر المختلفة.
        Count different types of lines.

        Args:
            lines: قائمة أسطر الملف - List of file lines

        Returns:
            _LineStats: إحصائيات الأسطر الأساسية
        """
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

        return _LineStats(
            code_lines=code_lines,
            comment_lines=comment_lines,
            blank_lines=blank_lines,
        )

    def _calculate_complexity_stats(self, functions: list[dict]) -> _ComplexityStats:
        """
        حساب إحصائيات التعقيد والتداخل.

        Args:
            functions: قائمة معلومات الدوال

        Returns:
            _ComplexityStats: ملخص التعقيد والتداخل
        """
        function_complexities = [f["complexity"] for f in functions]
        nesting_depths = [f["nesting_depth"] for f in functions]

        if not function_complexities:
            return _ComplexityStats(
                avg_complexity=0.0,
                max_complexity=0,
                max_func_name="",
                std_dev=0.0,
                avg_nesting=0.0,
            )

        avg_complexity = sum(function_complexities) / len(function_complexities)
        max_complexity = max(function_complexities)

        # Find function with max complexity
        max_func_name = ""
        for f in functions:
            if f["complexity"] == max_complexity:
                max_func_name = f["name"]
                break

        # Calculate standard deviation
        std_dev = self._calculate_standard_deviation(function_complexities, avg_complexity)
        avg_nesting = sum(nesting_depths) / len(nesting_depths) if nesting_depths else 0.0

        return _ComplexityStats(
            avg_complexity=avg_complexity,
            max_complexity=max_complexity,
            max_func_name=max_func_name,
            std_dev=std_dev,
            avg_nesting=avg_nesting,
        )

    def _calculate_standard_deviation(self, values: list[float], mean: float) -> float:
        """
        حساب الانحراف المعياري لقائمة قيم.

        Args:
            values: القيم المراد حساب انحرافها المعياري
            mean: المتوسط الحسابي للقيم

        Returns:
            float: الانحراف المعياري
        """
        if len(values) <= 1:
            return 0.0
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        return variance**0.5

    def _create_base_metrics(
        self,
        file_path: Path,
        lines: list[str],
        analyzer: ComplexityAnalyzer,
        line_stats: _LineStats,
        complexity_stats: _ComplexityStats,
    ) -> FileMetrics:
        """
        إنشاء كائن FileMetrics الأساسي.

        Args:
            file_path: مسار الملف
            lines: أسطر الملف
            analyzer: محلل التعقيد
            line_stats: إحصائيات الأسطر الأساسية
            complexity_stats: إحصائيات التعقيد والتداخل

        Returns:
            FileMetrics: كائن المقاييس الأساسية
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
        إثراء المقاييس بمعلومات Git.

        Args:
            metrics: كائن المقاييس للإثراء
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
        إثراء المقاييس بالروائح البنيوية.

        Args:
            metrics: كائن المقاييس للإثراء
            imports: قائمة الاستيرادات
        """
        smells = self.smell_detector.detect_smells(metrics.relative_path, metrics, imports)
        metrics.is_god_class = smells["is_god_class"]
        metrics.has_layer_mixing = smells["has_layer_mixing"]
        metrics.has_cross_layer_imports = smells["has_cross_layer_imports"]

    def analyze_file(self, file_path: Path) -> FileMetrics | None:
        """
        تحليل شامل لملف واحد.

        تم التحسين: تقسيم الدالة إلى helper methods حسب KISS principle

        Args:
            file_path: مسار الملف للتحليل

        Returns:
            FileMetrics أو None: مقاييس الملف أو None عند الفشل
        """
        try:
            content, lines = self._read_file_content(file_path)

            # حساب الأسطر
            line_stats = self._count_lines(lines)

            # تحليل AST
            tree = ast.parse(content)
            analyzer = ComplexityAnalyzer()
            analyzer.visit(tree)

            # حساب الإحصائيات
            complexity_stats = self._calculate_complexity_stats(analyzer.functions)

            # إنشاء كائن المقاييس الأساسي
            metrics = self._create_base_metrics(
                file_path,
                lines,
                analyzer,
                line_stats,
                complexity_stats,
            )

            # إثراء بمقاييس Git
            self._enrich_with_git_metrics(metrics)

            # إثراء بالروائح البنيوية
            self._enrich_with_smells(metrics, analyzer.imports)

            return metrics

        except (OSError, UnicodeDecodeError, SyntaxError, ValueError) as exc:
            logger.warning("تعذر تحليل الملف: %s بسبب %s", file_path, exc)
            return None

    def _read_file_content(self, file_path: Path) -> tuple[str, list[str]]:
        """
        قراءة محتوى الملف وتحويله إلى أسطر.

        Args:
            file_path: مسار الملف

        Returns:
            tuple[str, list[str]]: المحتوى الكامل وقائمة الأسطر
        """
        with open(file_path, encoding="utf-8") as file_handle:
            content = file_handle.read()
        return content, content.split("\n")

    def calculate_hotspot_scores(self, all_metrics: list[FileMetrics]) -> None:
        """
        حساب درجات النقاط الساخنة | Calculate hotspot scores with normalization

        يقوم بتطبيع القيم وحساب الدرجات الموزونة
        Normalizes values and calculates weighted scores

        Args:
            all_metrics: قائمة مقاييس الملفات | List of file metrics
        """
        if not all_metrics:
            return

        # Extract and normalize values
        ranks = self._extract_and_normalize_metrics(all_metrics)

        # Calculate scores and assign priorities
        self._calculate_weighted_scores(all_metrics, ranks)

    def _extract_and_normalize_metrics(self, all_metrics: list[FileMetrics]) -> _NormalizedRanks:
        """
        استخراج وتطبيع المقاييس | Extract and normalize metrics

        Args:
            all_metrics: قائمة المقاييس | Metrics list

        Returns:
            _NormalizedRanks: القيم المطبعة لكل فئة
        """
        # Extract values
        complexities = [m.file_complexity for m in all_metrics]
        volatilities = [m.commits_last_12months for m in all_metrics]
        smells = [self._count_smells(m) for m in all_metrics]

        # Normalize
        return _NormalizedRanks(
            complexity=self._normalize_values(complexities),
            volatility=self._normalize_values(volatilities),
            smell=self._normalize_values(smells),
        )

    def _count_smells(self, metrics: FileMetrics) -> int:
        """
        عد الروائح البنيوية | Count structural smells

        Args:
            metrics: مقاييس الملف | File metrics

        Returns:
            عدد الروائح | Number of smells
        """
        return (
            (1 if metrics.is_god_class else 0)
            + (1 if metrics.has_layer_mixing else 0)
            + (1 if metrics.has_cross_layer_imports else 0)
        )

    def _normalize_values(self, values: list[float]) -> list[float]:
        """
        تطبيع القيم إلى نطاق 0-1 | Normalize values to 0-1 range

        Args:
            values: قائمة القيم | List of values

        Returns:
            قائمة القيم المطبعة | List of normalized values
        """
        if not values or max(values) == 0:
            return [0.0] * len(values)
        max_val = max(values)
        return [v / max_val for v in values]

    def _calculate_weighted_scores(
        self,
        all_metrics: list[FileMetrics],
        ranks: _NormalizedRanks,
    ) -> None:
        """
        حساب الدرجات الموزونة | Calculate weighted scores

        Args:
            all_metrics: قائمة المقاييس | Metrics list
            ranks: القيم المطبعة | Normalized ranks
        """
        config = self._hotspot_config()
        for i, metrics in enumerate(all_metrics):
            self._assign_metric_ranks(metrics, ranks, i)
            score = self._calculate_hotspot_score(ranks, i, config.weights)
            metrics.hotspot_score = round(score, 4)
            metrics.priority_tier = self._determine_priority_tier(score)

    def _hotspot_config(self) -> _HotspotConfig:
        """
        إنشاء إعدادات النقاط الساخنة بطريقة موحدة.

        Returns:
            _HotspotConfig: إعدادات النقاط الساخنة
        """
        return _HotspotConfig(
            weights=_HotspotWeights(complexity=0.4, volatility=0.4, smell=0.2),
        )

    def _assign_metric_ranks(
        self,
        metrics: FileMetrics,
        ranks: _NormalizedRanks,
        index: int,
    ) -> None:
        """
        حفظ الرتب المعيارية لكل ملف.

        Args:
            metrics: مقاييس الملف | File metrics
            ranks: القيم المطبعة | Normalized ranks
            index: موضع الملف في القائمة
        """
        metrics.complexity_rank = round(ranks.complexity[index], 4)
        metrics.volatility_rank = round(ranks.volatility[index], 4)
        metrics.smell_rank = round(ranks.smell[index], 4)

    def _calculate_hotspot_score(
        self,
        ranks: _NormalizedRanks,
        index: int,
        weights: _HotspotWeights,
    ) -> float:
        """
        حساب درجة النقطة الساخنة لملف واحد.

        Args:
            ranks: القيم المطبعة | Normalized ranks
            index: موضع الملف في القائمة
            weights: أوزان الحساب

        Returns:
            float: الدرجة الموزونة
        """
        return (
            weights.complexity * ranks.complexity[index]
            + weights.volatility * ranks.volatility[index]
            + weights.smell * ranks.smell[index]
        )

    def _determine_priority_tier(self, score: float) -> str:
        """
        تحديد مستوى الأولوية | Determine priority tier

        Args:
            score: درجة النقطة الساخنة | Hotspot score

        Returns:
            مستوى الأولوية | Priority tier
        """
        if score >= 0.7:
            return "CRITICAL"
        if score >= 0.5:
            return "HIGH"
        if score >= 0.3:
            return "MEDIUM"
        return "LOW"

    def analyze_project(self) -> ProjectAnalysis:
        """
        تحليل المشروع بالكامل | Analyze entire project

        يقوم بتحليل جميع الملفات وحساب المقاييس
        Analyzes all files and calculates metrics

        Returns:
            تحليل المشروع | Project analysis
        """
        self._print_analysis_header()
        all_metrics = self._collect_file_metrics()
        self._calculate_and_sort_hotspots(all_metrics)
        return self._build_project_analysis(all_metrics)

    def _print_analysis_header(self) -> None:
        """
        طباعة رأس التحليل | Print analysis header
        """
        logger.info("🔍 Starting Structural Code Intelligence Analysis...")
        logger.info("📁 Repository: %s", self.repo_path)
        logger.info("🎯 Target paths: %s", ", ".join(self.target_paths))

    def _collect_file_metrics(self) -> list[FileMetrics]:
        """
        جمع مقاييس الملفات | Collect file metrics

        يقوم بالعثور على جميع الملفات وتحليلها
        Finds and analyzes all files

        Returns:
            قائمة المقاييس | List of metrics
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
        إرجاع قائمة ملفات بايثون داخل المسار المستهدف.

        Args:
            target_path: المسار المستهدف

        Returns:
            list[Path]: قائمة الملفات المكتشفة
        """
        return list(target_path.rglob("*.py"))

    def _analyze_target_path(self, target_path: Path, all_metrics: list[FileMetrics]) -> None:
        """
        تحليل مسار مستهدف | Analyze target path

        Args:
            target_path: المسار المستهدف | Target path
            all_metrics: قائمة المقاييس | Metrics list
        """
        for py_file in self._iter_python_files(target_path):
            if self.should_analyze(py_file):
                metrics = self.analyze_file(py_file)
                if metrics:
                    all_metrics.append(metrics)
                    logger.info("  ✓ %s", metrics.relative_path)

    def _calculate_and_sort_hotspots(self, all_metrics: list[FileMetrics]) -> None:
        """
        حساب وترتيب النقاط الساخنة | Calculate and sort hotspots

        Args:
            all_metrics: قائمة المقاييس | Metrics list
        """
        logger.info("📊 Calculating hotspot scores...")
        self.calculate_hotspot_scores(all_metrics)
        all_metrics.sort(key=lambda m: m.hotspot_score, reverse=True)

    def _build_project_analysis(self, all_metrics: list[FileMetrics]) -> ProjectAnalysis:
        """
        بناء تحليل المشروع | Build project analysis

        يحسب الإحصائيات الإجمالية ويحدد النقاط الساخنة
        Calculates overall statistics and identifies hotspots

        Args:
            all_metrics: قائمة المقاييس | Metrics list

        Returns:
            تحليل المشروع | Project analysis
        """
        stats = self._calculate_project_statistics(all_metrics)
        hotspots = self._identify_hotspots(all_metrics)

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

    def _calculate_project_statistics(self, all_metrics: list[FileMetrics]) -> _ProjectStats:
        """
        حساب إحصائيات المشروع | Calculate project statistics

        Args:
            all_metrics: قائمة المقاييس | Metrics list

        Returns:
            _ProjectStats: إحصائيات المشروع
        """
        avg_complexity = self._calculate_average_complexity(all_metrics)
        return _ProjectStats(
            total_lines=sum(m.total_lines for m in all_metrics),
            total_code=sum(m.code_lines for m in all_metrics),
            total_functions=sum(m.num_functions for m in all_metrics),
            total_classes=sum(m.num_classes for m in all_metrics),
            avg_complexity=round(avg_complexity, 2),
            max_complexity=max((m.file_complexity for m in all_metrics), default=0),
        )

    def _calculate_average_complexity(self, all_metrics: list[FileMetrics]) -> float:
        """
        حساب متوسط تعقيد الملفات.

        Args:
            all_metrics: قائمة المقاييس | Metrics list

        Returns:
            float: متوسط التعقيد
        """
        if not all_metrics:
            return 0.0
        return sum(m.file_complexity for m in all_metrics) / len(all_metrics)

    def _identify_hotspots(self, all_metrics: list[FileMetrics]) -> _HotspotBuckets:
        """
        تحديد النقاط الساخنة | Identify hotspots

        Args:
            all_metrics: قائمة المقاييس المرتبة | Sorted metrics list

        Returns:
            _HotspotBuckets: القوائم المصنفة للنقاط الساخنة
        """
        return _HotspotBuckets(
            critical=[m.relative_path for m in all_metrics[:20]],
            high=[m.relative_path for m in all_metrics[20:40]],
        )
