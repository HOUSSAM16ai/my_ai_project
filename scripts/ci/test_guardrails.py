"""اختبارات مستقلة للحواجز المعمارية لضمان سلامة الاستيراد والقاعدة."""

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if REPO_ROOT.as_posix() not in sys.path:
    sys.path.insert(0, REPO_ROOT.as_posix())

from scripts import ci_guardrails


class TestGuardrails(unittest.TestCase):
    """يتحقق من قواعد الحواجز عبر ملفات مؤقتة بسيطة."""

    def _write_file(self, base: Path, relative: str, content: str) -> Path:
        """ينشئ ملفًا مؤقتًا داخل المسار المعطى ويعيد مساره."""
        file_path = base / relative
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return file_path

    def test_cross_service_import_detection(self) -> None:
        """يتأكد من حظر الاستيراد بين الخدمات المختلفة."""
        with tempfile.TemporaryDirectory() as tmpdirname:
            root = Path(tmpdirname)
            violating_file = self._write_file(
                root,
                "microservices/order_service/bad.py",
                "from microservices.user_service import models\n",
            )

            errors = ci_guardrails.check_file(violating_file)

            self.assertTrue(any("Cross-service import forbidden" in e for e in errors))

    def test_forbidden_create_async_engine(self) -> None:
        """يتأكد من منع إنشاء المحرك مباشرة خارج المسارات المسموحة."""
        with tempfile.TemporaryDirectory() as tmpdirname:
            root = Path(tmpdirname)
            violating_file = self._write_file(
                root,
                "app/infrastructure/db_factory.py",
                "from sqlalchemy.ext.asyncio import create_async_engine\n"
                "engine = create_async_engine('sqlite+aiosqlite://')\n",
            )

            errors = ci_guardrails.check_file(violating_file)

            self.assertTrue(any("create_async_engine" in e for e in errors))

    def test_allow_create_engine_in_scripts(self) -> None:
        """يسمح للمخططات والصيانة في scripts باستخدام create_engine."""
        with tempfile.TemporaryDirectory() as tmpdirname:
            root = Path(tmpdirname)
            script_file = self._write_file(
                root,
                "scripts/db_maintenance.py",
                "from sqlalchemy import create_engine\nengine = create_engine('sqlite://')\n",
            )

            errors = ci_guardrails.check_file(script_file)

            self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
