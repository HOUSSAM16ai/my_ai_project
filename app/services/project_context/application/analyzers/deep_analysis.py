"""
Deep File Analysis
==================
Deep analysis of file content.
"""

from dataclasses import dataclass
from pathlib import Path

from app.services.project_context.domain.models import FileAnalysis

@dataclass
class DeepFileAnalyzer:
    """Analyzer for deep file analysis."""

    project_root: Path

    def analyze(self) -> FileAnalysis:
        """
        تحليل عميق لجميع الملفات.
        Deep analyze all files.
        
        Returns:
            FileAnalysis: نتائج التحليل العميق | Deep analysis results
        """
        analysis = FileAnalysis()
        app_dir = self.project_root / "app"
        
        if not app_dir.exists():
            return analysis

        for py_file in self._iterate_python_files(app_dir):
            self._analyze_file(py_file, analysis)

        return analysis

    def _iterate_python_files(self, app_dir: Path):
        """
        التكرار عبر ملفات Python.
        Iterate through Python files.
        
        Args:
            app_dir: مسار دليل التطبيق | Application directory path
            
        Yields:
            Path: مسار ملف Python | Python file path
        """
        for py_file in app_dir.rglob("*.py"):
            if "__pycache__" not in str(py_file):
                yield py_file

    def _analyze_file(self, py_file: Path, analysis: FileAnalysis) -> None:
        """
        تحليل ملف واحد.
        Analyze a single file.
        
        Args:
            py_file: مسار الملف | File path
            analysis: كائن التحليل للتحديث | Analysis object to update
        """
        try:
            content = py_file.read_text(encoding="utf-8")
            self._count_code_elements(content, analysis)
            self._detect_frameworks(content, analysis)
            self._detect_design_patterns(content, analysis)
        except Exception:
            pass

    def _count_code_elements(self, content: str, analysis: FileAnalysis) -> None:
        """
        عد عناصر الكود.
        Count code elements.
        
        Args:
            content: محتوى الملف | File content
            analysis: كائن التحليل | Analysis object
        """
        analysis.total_classes += content.count("\nclass ")
        analysis.total_functions += content.count("\ndef ") + content.count("\nasync def ")
        analysis.total_imports += content.count("\nimport ") + content.count("\nfrom ")

    def _detect_frameworks(self, content: str, analysis: FileAnalysis) -> None:
        """
        كشف الأطر المستخدمة.
        Detect frameworks used.
        
        Args:
            content: محتوى الملف | File content
            analysis: كائن التحليل | Analysis object
        """
        framework_checks = [
            ("fastapi", "FastAPI"),
            ("sqlalchemy", "SQLAlchemy"),
            ("pydantic", "Pydantic"),
        ]
        
        for keyword, framework_name in framework_checks:
            if keyword in content.lower() and framework_name not in analysis.frameworks_detected:
                analysis.frameworks_detected.append(framework_name)

    def _detect_design_patterns(self, content: str, analysis: FileAnalysis) -> None:
        """
        كشف أنماط التصميم.
        Detect design patterns.
        
        Args:
            content: محتوى الملف | File content
            analysis: كائن التحليل | Analysis object
        """
        pattern_checks = [
            ("Factory", "Factory Pattern"),
            ("@dataclass", "Dataclass"),
            ("Singleton", "Singleton Pattern"),
            ("_instance", "Singleton Pattern"),
            ("async def", "Async/Await"),
        ]
        
        for keyword, pattern_name in pattern_checks:
            if keyword in content and pattern_name not in analysis.design_patterns:
                analysis.design_patterns.append(pattern_name)
                # Break after finding Singleton pattern to avoid duplicates
                if pattern_name == "Singleton Pattern" and "Singleton" in keyword:
                    break
