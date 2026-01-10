"""اختبارات ماسح الحواجز المعمارية للـ CI."""

import tempfile
from pathlib import Path

from scripts import ci_guardrails


def test_detects_cross_service_import() -> None:
    """يتحقق من رصد الاستيراد بين الخدمات."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        service_dir = root / "microservices" / "orders"
        service_dir.mkdir(parents=True)
        violating_file = service_dir / "bad.py"
        violating_file.write_text("from microservices.users import models\n", encoding="utf-8")

        errors = ci_guardrails.check_file(violating_file)

        assert any("Cross-service import forbidden" in error for error in errors)


def test_detects_adhoc_engine_creation() -> None:
    """يتحقق من منع إنشاء محرك قاعدة بيانات خارج المصنع."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        violating_file = root / "service.py"
        violating_file.write_text("engine = create_async_engine('sqlite://')\n", encoding="utf-8")

        errors = ci_guardrails.check_file(violating_file)

        assert any("create_async_engine" in error for error in errors)


def test_allows_print_in_scripts_paths() -> None:
    """يتحقق من سماح الطباعة داخل مجلد scripts فقط."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        script_dir = root / "scripts"
        script_dir.mkdir()
        script_file = script_dir / "task.py"
        script_file.write_text("print('ok')\n", encoding="utf-8")

        errors = ci_guardrails.check_file(script_file)

        assert not any("print" in error for error in errors)
