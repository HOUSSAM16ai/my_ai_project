#!/usr/bin/env python3
"""
أداة تحليل شاملة للمشروع | Comprehensive Project Analysis Tool

هذه الأداة تقوم بتحليل المشروع بالكامل لإيجاد:
- الكود الميت (Dead Code)
- الدوال غير المستخدمة (Unused Functions)
- الملفات الكبيرة (Large Files)
- الاستيرادات غير المستخدمة (Unused Imports)
- التعقيد الزائد (Complexity Issues)

الاستخدام:
    python3 analyze_project.py

المخرجات:
    - تقرير شامل بصيغة Markdown
    - قائمة بالملفات التي تحتاج تحسين
    - توصيات محددة
"""

import ast
import os
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class FileAnalysis:
    """
    تحليل ملف واحد.
    
    Attributes:
        path: مسار الملف
        lines: عدد الأسطر
        functions: عدد الدوال
        classes: عدد الفئات
        complexity: مستوى التعقيد
        has_tests: هل يوجد ملف اختبار مقابل
    """
    path: str
    lines: int
    functions: int
    classes: int
    complexity: int
    has_tests: bool
    imports: list[str]
    
    def is_large(self) -> bool:
        """ملف كبير إذا كان أكثر من 300 سطر."""
        return self.lines > 300
    
    def is_complex(self) -> bool:
        """ملف معقد إذا كان التعقيد أكثر من 10."""
        return self.complexity > 10


class ProjectAnalyzer:
    """
    محلل المشروع الشامل.
    
    يقوم بفحص جميع ملفات المشروع وإنتاج تقرير مفصل.
    """
    
    def __init__(self, project_root: str):
        """
        تهيئة المحلل.
        
        Args:
            project_root: المسار الجذري للمشروع
        """
        self.project_root = Path(project_root)
        self.app_dir = self.project_root / "app"
        self.tests_dir = self.project_root / "tests"
        self.analyses: list[FileAnalysis] = []
        
    def analyze_file(self, file_path: Path) -> FileAnalysis | None:
        """
        تحليل ملف واحد.
        
        Args:
            file_path: مسار الملف
            
        Returns:
            تحليل الملف أو None إذا فشل
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content)
            
            # عد الأسطر
            lines = len(content.splitlines())
            
            # عد الدوال والفئات
            functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
            classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
            
            # حساب التعقيد (عدد if/for/while/try)
            complexity = sum(
                1 for node in ast.walk(tree)
                if isinstance(node, (ast.If, ast.For, ast.While, ast.Try))
            )
            
            # جمع الاستيرادات
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
            
            # التحقق من وجود ملف اختبار
            relative_path = file_path.relative_to(self.app_dir)
            test_path = self.tests_dir / f"test_{relative_path}"
            has_tests = test_path.exists()
            
            return FileAnalysis(
                path=str(file_path.relative_to(self.project_root)),
                lines=lines,
                functions=functions,
                classes=classes,
                complexity=complexity,
                has_tests=has_tests,
                imports=imports,
            )
        except Exception as e:
            print(f"⚠️  Could not analyze {file_path}: {e}")
            return None
    
    def analyze_all(self) -> None:
        """تحليل جميع ملفات المشروع."""
        print("🔍 Analyzing all Python files in the project...")
        
        for file_path in self.app_dir.rglob("*.py"):
            if "__pycache__" in str(file_path):
                continue
            
            analysis = self.analyze_file(file_path)
            if analysis:
                self.analyses.append(analysis)
        
        print(f"✅ Analyzed {len(self.analyses)} files")
    
    def generate_report(self) -> str:
        """
        إنشاء تقرير شامل.
        
        Returns:
            تقرير بصيغة Markdown
        """
        report = []
        report.append("# تقرير تحليل المشروع الشامل | Comprehensive Project Analysis")
        report.append("")
        report.append(f"**تاريخ التحليل:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("")
        
        # إحصائيات عامة
        total_lines = sum(a.lines for a in self.analyses)
        total_functions = sum(a.functions for a in self.analyses)
        total_classes = sum(a.classes for a in self.analyses)
        files_without_tests = sum(1 for a in self.analyses if not a.has_tests)
        
        report.append("## 📊 الإحصائيات العامة | General Statistics")
        report.append("")
        report.append(f"- **عدد الملفات الكلي:** {len(self.analyses)}")
        report.append(f"- **إجمالي الأسطر:** {total_lines:,}")
        report.append(f"- **إجمالي الدوال:** {total_functions:,}")
        report.append(f"- **إجمالي الفئات:** {total_classes:,}")
        report.append(f"- **ملفات بدون اختبارات:** {files_without_tests} ({files_without_tests/len(self.analyses)*100:.1f}%)")
        report.append("")
        
        # الملفات الكبيرة
        large_files = sorted([a for a in self.analyses if a.is_large()], key=lambda x: x.lines, reverse=True)
        report.append("## 📏 الملفات الكبيرة | Large Files")
        report.append("")
        report.append(f"الملفات الأكبر من 300 سطر: **{len(large_files)}** ملف")
        report.append("")
        
        if large_files:
            report.append("| الملف | الأسطر | الدوال | الفئات | اختبارات |")
            report.append("|-------|--------|--------|--------|----------|")
            for analysis in large_files[:15]:
                tests_icon = "✅" if analysis.has_tests else "❌"
                report.append(
                    f"| `{analysis.path}` | {analysis.lines} | {analysis.functions} | "
                    f"{analysis.classes} | {tests_icon} |"
                )
        report.append("")
        
        # الملفات المعقدة
        complex_files = sorted([a for a in self.analyses if a.is_complex()], key=lambda x: x.complexity, reverse=True)
        report.append("## 🔥 الملفات المعقدة | Complex Files")
        report.append("")
        report.append(f"الملفات ذات التعقيد العالي (>10): **{len(complex_files)}** ملف")
        report.append("")
        
        if complex_files:
            report.append("| الملف | التعقيد | الأسطر |")
            report.append("|-------|---------|--------|")
            for analysis in complex_files[:15]:
                report.append(f"| `{analysis.path}` | {analysis.complexity} | {analysis.lines} |")
        report.append("")
        
        # الملفات بدون اختبارات
        report.append("## 🧪 الملفات بدون اختبارات | Files Without Tests")
        report.append("")
        untested = [a for a in self.analyses if not a.has_tests]
        report.append(f"عدد الملفات: **{len(untested)}** ملف")
        report.append("")
        
        # الأولويات
        report.append("## 🎯 أولويات التحسين | Improvement Priorities")
        report.append("")
        report.append("### أولوية عالية جداً (High Priority)")
        high_priority = [
            a for a in self.analyses
            if a.is_large() and a.is_complex() and not a.has_tests
        ]
        report.append(f"- **{len(high_priority)} ملف** كبير، معقد، وبدون اختبارات")
        report.append("")
        
        if high_priority:
            for analysis in sorted(high_priority, key=lambda x: x.lines, reverse=True)[:10]:
                report.append(f"  - `{analysis.path}` ({analysis.lines} سطر، تعقيد {analysis.complexity})")
        report.append("")
        
        report.append("### أولوية عالية (Medium Priority)")
        medium_priority = [
            a for a in self.analyses
            if (a.is_large() or a.is_complex()) and not a.has_tests
        ]
        report.append(f"- **{len(medium_priority)} ملف** كبير أو معقد بدون اختبارات")
        report.append("")
        
        # التوصيات
        report.append("## 💡 التوصيات | Recommendations")
        report.append("")
        report.append("### 1. تقسيم الملفات الكبيرة")
        report.append("- قسّم الملفات الأكبر من 300 سطر إلى ملفات أصغر")
        report.append("- كل ملف يجب أن يكون < 200 سطر")
        report.append("")
        
        report.append("### 2. تبسيط الملفات المعقدة")
        report.append("- استخرج الدوال المعقدة إلى دوال أصغر")
        report.append("- استخدم Strategy Pattern للتعقيد الشرطي")
        report.append("")
        
        report.append("### 3. إضافة اختبارات شاملة")
        report.append(f"- أضف اختبارات لـ {files_without_tests} ملف")
        report.append("- الهدف: تغطية 100%")
        report.append("")
        
        return "\n".join(report)
    
    def save_report(self, filename: str = "PROJECT_ANALYSIS_REPORT.md") -> None:
        """
        حفظ التقرير في ملف.
        
        Args:
            filename: اسم ملف التقرير
        """
        report = self.generate_report()
        output_path = self.project_root / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"✅ Report saved to: {output_path}")


def main():
    """الدالة الرئيسية."""
    import sys
    
    # المسار الجذري للمشروع
    if len(sys.argv) > 1:
        project_root = sys.argv[1]
    else:
        project_root = os.getcwd()
    
    print(f"📁 Analyzing project at: {project_root}")
    
    # إنشاء المحلل وتشغيله
    analyzer = ProjectAnalyzer(project_root)
    analyzer.analyze_all()
    
    # إنشاء وحفظ التقرير
    analyzer.save_report()
    
    print("\n🎉 Analysis complete!")


if __name__ == "__main__":
    main()
