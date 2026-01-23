"""
اختبارات محللات سياق المشروع.
"""

from dataclasses import dataclass

import pytest

from app.services.project_context.application.analyzers.issues import (
    IssueAnalyzer,
    LONG_METHOD_LINE_THRESHOLD,
)
from app.services.project_context.application.analyzers.stats import CodeStatsAnalyzer
from app.services.project_context.application.analyzers.structure import StructureAnalyzer


@dataclass(frozen=True)
class MethodSpec:
    """وصف تجميعي لبناء دالة بعدد أسطر محدد بدقة."""

    name: str
    total_lines: int
    accumulator: str


def build_method_source(spec: MethodSpec) -> str:
    """ينشئ نص دالة بعدد أسطر إجمالي مضبوط وفق المواصفات."""
    if spec.total_lines < 3:
        raise ValueError("يجب أن يشمل العدد أسطر التعريف والجسم والإرجاع.")
    body_lines = spec.total_lines - 2
    if body_lines < 1:
        raise ValueError("يجب أن يحتوي جسم الدالة على سطر واحد على الأقل.")
    body = [f"    {spec.accumulator} = 0"] + [
        f"    {spec.accumulator} += 1" for _ in range(body_lines - 1)
    ]
    return (
        f"def {spec.name}():\n"
        + "\n".join(body)
        + f"\n    return {spec.accumulator}\n"
    )


def build_file_source(specs: list[MethodSpec]) -> str:
    """يبني محتوى ملف كامل اعتمادًا على مواصفات الدوال."""
    return "".join(build_method_source(spec) for spec in specs)


@pytest.fixture
def project_root(tmp_path):
    """يبني بنية مشروع اختبارية مصغرة للاستخدام داخل الاختبارات."""
    app_dir = tmp_path / "app"
    app_dir.mkdir()

    # ملف بايثون أساسي
    (app_dir / "main.py").write_text("print('hello')\n", encoding="utf-8")

    # مجلد فرعي يحوي ملف بايثون
    services_dir = app_dir / "services"
    services_dir.mkdir()
    (services_dir / "service.py").write_text("def test():\n    pass\n", encoding="utf-8")

    # ملف مخفي للاختبارات
    (app_dir / "__init__.py").write_text("", encoding="utf-8")

    # مجلد اختبارات داخلي
    tests_dir = tmp_path / "tests"
    tests_dir.mkdir()
    (tests_dir / "test_main.py").write_text("def test_main():\n    pass\n", encoding="utf-8")

    return tmp_path


def test_code_stats_analyzer(project_root):
    """يتحقق من حساب الإحصاءات الأساسية لملفات المشروع."""
    analyzer = CodeStatsAnalyzer(project_root)
    stats = analyzer.analyze()

    # المنطق الحالي يعتمد على: `if "__pycache__" not in str(py_file)`
    # لذلك لا يتم استثناء __init__.py إلا بتعامل صريح منفصل.
    # بالتالي ملفات التطبيق تشمل main.py و service.py و __init__.py.
    # ملفات الاختبارات تشمل test_main.py.

    assert stats.python_files >= 2
    assert stats.test_files == 1
    assert stats.app_lines > 0


def test_structure_analyzer(project_root):
    """يتحقق من تحليل البنية واكتشاف الأدلة الفرعية المطلوبة."""
    analyzer = StructureAnalyzer(project_root)
    structure = analyzer.analyze()

    # يجب العثور على مجلد services داخل app
    service_dir_found = False
    for d in structure.directories:
        if d.name == "services":
            service_dir_found = True
            assert d.file_count == 1  # ملف service.py

    assert service_dir_found


def test_issue_analyzer(project_root):
    """يتحقق من اكتشاف المخالفات الأسلوبية المتوقعة."""
    # إنشاء ملف يحوي مخالفات أسلوبية
    bad_file = project_root / "app" / "bad.py"
    bad_file.write_text("import os\nprint('debug')\n", encoding="utf-8")

    analyzer = IssueAnalyzer(project_root)
    issues = analyzer.deep_search_issues()

    # يجب اكتشاف تعليمة الطباعة
    found_print = any(issue.issue_type == "print_statement" for issue in issues.style_issues)

    assert found_print


def test_issue_analyzer_detects_long_method_at_file_end(project_root):
    """يتأكد من شمول آخر دالة في الملف ضمن كشف الدوال الطويلة."""
    long_method_file = project_root / "app" / "long_method.py"
    long_method_file.write_text(
        build_file_source(
            [
                MethodSpec(
                    name="long_task",
                    total_lines=LONG_METHOD_LINE_THRESHOLD + 10,
                    accumulator="total",
                )
            ]
        ),
        encoding="utf-8",
    )

    analyzer = IssueAnalyzer(project_root)
    smells = analyzer.detect_code_smells()

    assert any(smell.method == "long_task" for smell in smells.long_methods)


def test_issue_analyzer_long_method_threshold_boundary(project_root):
    """يتحقق من احترام حدود العتبة في كشف الدوال الطويلة."""
    boundary_file = project_root / "app" / "boundary.py"
    boundary_file.write_text(
        build_file_source(
            [
                MethodSpec(
                    name="at_limit",
                    total_lines=LONG_METHOD_LINE_THRESHOLD,
                    accumulator="value",
                ),
                MethodSpec(
                    name="over_limit",
                    total_lines=LONG_METHOD_LINE_THRESHOLD + 1,
                    accumulator="total",
                ),
            ]
        ),
        encoding="utf-8",
    )

    analyzer = IssueAnalyzer(project_root)
    smells = analyzer.detect_code_smells()

    flagged = {smell.method for smell in smells.long_methods}
    assert "over_limit" in flagged
    assert "at_limit" not in flagged
