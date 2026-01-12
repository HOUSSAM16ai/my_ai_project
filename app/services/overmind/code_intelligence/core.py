import ast
from datetime import datetime
from pathlib import Path

from .analyzers.complexity import ComplexityAnalyzer
from .analyzers.git import GitAnalyzer
from .analyzers.smells import StructuralSmellDetector
from .models import FileMetrics, ProjectAnalysis


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

    def _count_lines(self, lines: list[str]) -> tuple[int, int, int]:
        """
        حساب أنواع الأسطر المختلفة.
        Count different types of lines.

        Args:
            lines: قائمة أسطر الملف - List of file lines

        Returns:
            tuple: (code_lines, comment_lines, blank_lines)
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

        return code_lines, comment_lines, blank_lines

    def _calculate_complexity_stats(self, functions: list[dict]) -> tuple[float, int, str, float]:
        """
        حساب إحصائيات التعقيد.

        Args:
            functions: قائمة معلومات الدوال

        Returns:
            tuple: (avg_complexity, max_complexity, max_func_name, std_dev)
        """
        function_complexities = [f["complexity"] for f in functions]

        if not function_complexities:
            return 0.0, 0, "", 0.0

        avg_complexity = sum(function_complexities) / len(function_complexities)
        max_complexity = max(function_complexities)

        # Find function with max complexity
        max_func_name = ""
        for f in functions:
            if f["complexity"] == max_complexity:
                max_func_name = f["name"]
                break

        # Calculate standard deviation
        if len(function_complexities) > 1:
            mean = avg_complexity
            variance = sum((x - mean) ** 2 for x in function_complexities) / len(
                function_complexities
            )
            std_dev = variance**0.5
        else:
            std_dev = 0.0

        return avg_complexity, max_complexity, max_func_name, std_dev

    def _calculate_nesting_stats(self, functions: list[dict]) -> float:
        """
        حساب إحصائيات التداخل.

        Args:
            functions: قائمة معلومات الدوال

        Returns:
            float: متوسط عمق التداخل
        """
        nesting_depths = [f["nesting_depth"] for f in functions]
        return sum(nesting_depths) / len(nesting_depths) if nesting_depths else 0.0

    def _create_base_metrics(
        self,
        file_path: Path,
        lines: list[str],
        code_lines: int,
        comment_lines: int,
        blank_lines: int,
        analyzer: ComplexityAnalyzer,
        avg_complexity: float,
        max_complexity: int,
        max_func_name: str,
        std_dev: float,
        avg_nesting: float,
    ) -> FileMetrics:
        """
        إنشاء كائن FileMetrics الأساسي.

        Args:
            file_path: مسار الملف
            lines: أسطر الملف
            code_lines: عدد أسطر الكود
            comment_lines: عدد أسطر التعليقات
            blank_lines: عدد الأسطر الفارغة
            analyzer: محلل التعقيد
            avg_complexity: متوسط التعقيد
            max_complexity: أقصى تعقيد
            max_func_name: اسم الدالة الأكثر تعقيداً
            std_dev: الانحراف المعياري
            avg_nesting: متوسط التداخل

        Returns:
            FileMetrics: كائن المقاييس الأساسية
        """
        relative_path = str(file_path.relative_to(self.repo_path))

        return FileMetrics(
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
            # قراءة الملف
            with open(file_path, encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            # حساب الأسطر
            code_lines, comment_lines, blank_lines = self._count_lines(lines)

            # تحليل AST
            tree = ast.parse(content)
            analyzer = ComplexityAnalyzer()
            analyzer.visit(tree)

            # حساب الإحصائيات
            avg_complexity, max_complexity, max_func_name, std_dev = (
                self._calculate_complexity_stats(analyzer.functions)
            )
            avg_nesting = self._calculate_nesting_stats(analyzer.functions)

            # إنشاء كائن المقاييس الأساسي
            metrics = self._create_base_metrics(
                file_path,
                lines,
                code_lines,
                comment_lines,
                blank_lines,
                analyzer,
                avg_complexity,
                max_complexity,
                max_func_name,
                std_dev,
                avg_nesting,
            )

            # إثراء بمقاييس Git
            self._enrich_with_git_metrics(metrics)

            # إثراء بالروائح البنيوية
            self._enrich_with_smells(metrics, analyzer.imports)

            return metrics

        except Exception:
            # التعامل مع الأخطاء بصمت
            return None

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

    def _extract_and_normalize_metrics(self, all_metrics: list[FileMetrics]) -> dict:
        """
        استخراج وتطبيع المقاييس | Extract and normalize metrics

        Args:
            all_metrics: قائمة المقاييس | Metrics list

        Returns:
            معجم القيم المطبعة | Dictionary of normalized values
        """
        # Extract values
        complexities = [m.file_complexity for m in all_metrics]
        volatilities = [m.commits_last_12months for m in all_metrics]
        smells = [self._count_smells(m) for m in all_metrics]

        # Normalize
        return {
            "complexity": self._normalize_values(complexities),
            "volatility": self._normalize_values(volatilities),
            "smell": self._normalize_values(smells),
        }

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

    def _calculate_weighted_scores(self, all_metrics: list[FileMetrics], ranks: dict) -> None:
        """
        حساب الدرجات الموزونة | Calculate weighted scores

        Args:
            all_metrics: قائمة المقاييس | Metrics list
            ranks: القيم المطبعة | Normalized ranks
        """
        # Weight configuration: Complexity + Volatility + Smells
        w1, w2, w3 = 0.4, 0.4, 0.2

        for i, metrics in enumerate(all_metrics):
            # Store individual ranks
            metrics.complexity_rank = round(ranks["complexity"][i], 4)
            metrics.volatility_rank = round(ranks["volatility"][i], 4)
            metrics.smell_rank = round(ranks["smell"][i], 4)

            # Calculate weighted hotspot score
            score = (
                w1 * ranks["complexity"][i] + w2 * ranks["volatility"][i] + w3 * ranks["smell"][i]
            )
            metrics.hotspot_score = round(score, 4)

            # Assign priority tier
            metrics.priority_tier = self._determine_priority_tier(score)

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
        print("🔍 Starting Structural Code Intelligence Analysis...")
        print(f"📁 Repository: {self.repo_path}")
        print(f"🎯 Target paths: {', '.join(self.target_paths)}")
        print()

    def _collect_file_metrics(self) -> list:
        """
        جمع مقاييس الملفات | Collect file metrics

        يقوم بالعثور على جميع الملفات وتحليلها
        Finds and analyzes all files

        Returns:
            قائمة المقاييس | List of metrics
        """
        all_metrics = []

        for target in self.target_paths:
            target_path = self.repo_path / target
            if not target_path.exists():
                print(f"⚠️  Path not found: {target_path}")
                continue

            print(f"📂 Analyzing {target}...")
            self._analyze_target_path(target_path, all_metrics)

        print(f"\n✅ Analyzed {len(all_metrics)} files")
        return all_metrics

    def _analyze_target_path(self, target_path, all_metrics: list) -> None:
        """
        تحليل مسار مستهدف | Analyze target path

        Args:
            target_path: المسار المستهدف | Target path
            all_metrics: قائمة المقاييس | Metrics list
        """
        py_files = list(target_path.rglob("*.py"))
        for py_file in py_files:
            if self.should_analyze(py_file):
                metrics = self.analyze_file(py_file)
                if metrics:
                    all_metrics.append(metrics)
                    print(f"  ✓ {metrics.relative_path}")

    def _calculate_and_sort_hotspots(self, all_metrics: list) -> None:
        """
        حساب وترتيب النقاط الساخنة | Calculate and sort hotspots

        Args:
            all_metrics: قائمة المقاييس | Metrics list
        """
        print("\n📊 Calculating hotspot scores...")
        self.calculate_hotspot_scores(all_metrics)
        all_metrics.sort(key=lambda m: m.hotspot_score, reverse=True)

    def _build_project_analysis(self, all_metrics: list) -> ProjectAnalysis:
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
            total_lines=stats["total_lines"],
            total_code_lines=stats["total_code"],
            total_functions=stats["total_functions"],
            total_classes=stats["total_classes"],
            avg_file_complexity=stats["avg_complexity"],
            max_file_complexity=stats["max_complexity"],
            critical_hotspots=hotspots["critical"],
            high_hotspots=hotspots["high"],
            files=all_metrics,
        )

    def _calculate_project_statistics(self, all_metrics: list) -> dict:
        """
        حساب إحصائيات المشروع | Calculate project statistics

        Args:
            all_metrics: قائمة المقاييس | Metrics list

        Returns:
            معجم الإحصائيات | Statistics dictionary
        """
        return {
            "total_lines": sum(m.total_lines for m in all_metrics),
            "total_code": sum(m.code_lines for m in all_metrics),
            "total_functions": sum(m.num_functions for m in all_metrics),
            "total_classes": sum(m.num_classes for m in all_metrics),
            "avg_complexity": round(
                sum(m.file_complexity for m in all_metrics) / len(all_metrics)
                if all_metrics
                else 0,
                2,
            ),
            "max_complexity": max((m.file_complexity for m in all_metrics), default=0),
        }

    def _identify_hotspots(self, all_metrics: list) -> dict:
        """
        تحديد النقاط الساخنة | Identify hotspots

        Args:
            all_metrics: قائمة المقاييس المرتبة | Sorted metrics list

        Returns:
            معجم النقاط الساخنة | Hotspots dictionary
        """
        return {
            "critical": [m.relative_path for m in all_metrics[:20]],
            "high": [m.relative_path for m in all_metrics[20:40]],
        }
