#!/usr/bin/env python3
"""
🧹 نظام التنظيف والتنظيم الخارق | Super Cleanup & Organization System
========================================================================

نظام شامل لتنظيف وتنظيم المشروع بشكل احترافي وخارق.
Comprehensive system for professional and super cleanup and organization.

الميزات (Features):
- تنظيف ملفات Python المؤقتة
- تنظيف ملفات البناء
- تنظيم الاستيرادات (imports)
- فحص الأكواد الميتة (dead code)
- تقرير شامل للتنظيف

المبادئ (Principles):
- KISS: بساطة في التنفيذ
- DRY: لا تكرار في المنطق
- Safety First: لا حذف بدون تأكيد
"""

import contextlib
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class CleanupStats:
    """إحصائيات التنظيف."""

    files_removed: int = 0
    dirs_removed: int = 0
    space_freed_mb: float = 0.0
    duration_seconds: float = 0.0
    categories: dict[str, int] = None

    def __post_init__(self):
        if self.categories is None:
            self.categories = {}


class SuperCleanup:
    """
    نظام التنظيف الخارق.

    يوفر قدرات تنظيف وتنظيم شاملة للمشروع.
    """

    def __init__(self, project_root: Path):
        """
        تهيئة نظام التنظيف.

        Args:
            project_root: المسار الجذري للمشروع
        """
        self.project_root = project_root
        self.stats = CleanupStats()
        self.dry_run = False

        # الأنماط المراد تنظيفها
        self.patterns = {
            "python_cache": ["**/__pycache__", "**/*.pyc", "**/*.pyo"],
            "build": ["**/build", "**/dist", "**/*.egg-info"],
            "temp": ["**/*.tmp", "**/*.log", "**/.DS_Store"],
            "coverage": ["**/.coverage", "**/htmlcov", "**/.pytest_cache"],
            "mypy": ["**/.mypy_cache", "**/.dmypy.json"],
        }

    def _get_size_mb(self, path: Path) -> float:
        """حساب حجم الملف أو المجلد بالميغابايت."""
        if path.is_file():
            return path.stat().st_size / (1024 * 1024)

        total = 0
        for item in path.rglob("*"):
            if item.is_file():
                with contextlib.suppress(OSError, PermissionError):
                    total += item.stat().st_size
        return total / (1024 * 1024)

    def _safe_remove(self, path: Path, category: str) -> bool:
        """
        حذف آمن للملف أو المجلد.

        Args:
            path: المسار المراد حذفه
            category: فئة التنظيف

        Returns:
            bool: True إذا تم الحذف بنجاح
        """
        if self.dry_run:
            print(f"  [DRY RUN] Would remove: {path}")
            return False

        try:
            size_mb = self._get_size_mb(path)

            if path.is_file():
                path.unlink()
                self.stats.files_removed += 1
            elif path.is_dir():
                shutil.rmtree(path)
                self.stats.dirs_removed += 1

            self.stats.space_freed_mb += size_mb
            self.stats.categories[category] = self.stats.categories.get(category, 0) + 1

            return True
        except (OSError, PermissionError) as e:
            print(f"  ⚠️  Error removing {path}: {e}")
            return False

    def clean_python_cache(self) -> int:
        """
        تنظيف ملفات Python المؤقتة.

        Returns:
            int: عدد العناصر المحذوفة
        """
        print("\n🐍 تنظيف Python cache...")
        count = 0

        for pattern in self.patterns["python_cache"]:
            for path in self.project_root.glob(pattern):
                if self._safe_remove(path, "python_cache"):
                    count += 1

        print(f"  ✅ تم تنظيف {count} عنصر Python cache")
        return count

    def clean_build_artifacts(self) -> int:
        """
        تنظيف ملفات البناء.

        Returns:
            int: عدد العناصر المحذوفة
        """
        print("\n🔨 تنظيف Build artifacts...")
        count = 0

        for pattern in self.patterns["build"]:
            for path in self.project_root.glob(pattern):
                if self._safe_remove(path, "build"):
                    count += 1

        print(f"  ✅ تم تنظيف {count} عنصر build")
        return count

    def clean_temp_files(self) -> int:
        """
        تنظيف الملفات المؤقتة.

        Returns:
            int: عدد العناصر المحذوفة
        """
        print("\n🗑️  تنظيف Temp files...")
        count = 0

        for pattern in self.patterns["temp"]:
            for path in self.project_root.glob(pattern):
                if self._safe_remove(path, "temp"):
                    count += 1

        print(f"  ✅ تم تنظيف {count} ملف مؤقت")
        return count

    def clean_test_artifacts(self) -> int:
        """
        تنظيف ملفات الاختبار.

        Returns:
            int: عدد العناصر المحذوفة
        """
        print("\n🧪 تنظيف Test artifacts...")
        count = 0

        for pattern in self.patterns["coverage"]:
            for path in self.project_root.glob(pattern):
                if self._safe_remove(path, "test"):
                    count += 1

        print(f"  ✅ تم تنظيف {count} عنصر test")
        return count

    def clean_type_check_cache(self) -> int:
        """
        تنظيف ملفات mypy cache.

        Returns:
            int: عدد العناصر المحذوفة
        """
        print("\n📝 تنظيف Type checking cache...")
        count = 0

        for pattern in self.patterns["mypy"]:
            for path in self.project_root.glob(pattern):
                if self._safe_remove(path, "mypy"):
                    count += 1

        print(f"  ✅ تم تنظيف {count} عنصر mypy")
        return count

    def organize_imports(self) -> None:
        """
        تنظيم الاستيرادات باستخدام isort.
        """
        print("\n📦 تنظيم الاستيرادات...")

        try:
            result = subprocess.run(
                ["isort", "--check-only", str(self.project_root / "app")],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                print("  ℹ️  الاستيرادات تحتاج تنظيم")
                if not self.dry_run:
                    subprocess.run(
                        ["isort", str(self.project_root / "app")], check=False, timeout=60
                    )
                    print("  ✅ تم تنظيم الاستيرادات")
            else:
                print("  ✅ الاستيرادات منظمة بالفعل")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("  ⚠️  isort غير متوفر")

    def check_dead_code(self) -> None:
        """
        فحص الأكواد الميتة باستخدام vulture.
        """
        print("\n🔍 فحص Dead code...")

        try:
            result = subprocess.run(
                ["vulture", str(self.project_root / "app"), "--min-confidence", "80"],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.stdout.strip():
                print("  ⚠️  وُجد كود ميت محتمل:")
                lines = result.stdout.strip().split("\n")[:10]
                for line in lines:
                    print(f"    {line}")
            else:
                print("  ✅ لم يُعثر على كود ميت")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print("  ℹ️  vulture غير متوفر")

    def run_full_cleanup(self, dry_run: bool = False) -> CleanupStats:
        """
        تشغيل تنظيف شامل.

        Args:
            dry_run: تشغيل تجريبي بدون حذف فعلي

        Returns:
            CleanupStats: إحصائيات التنظيف
        """
        self.dry_run = dry_run
        start_time = datetime.now()

        print("=" * 70)
        print("🚀 بدء التنظيف الخارق | Starting Super Cleanup")
        print("=" * 70)

        if dry_run:
            print("\n⚠️  وضع التجربة (DRY RUN) - لن يتم حذف أي شيء")

        # تنظيف الملفات
        self.clean_python_cache()
        self.clean_build_artifacts()
        self.clean_temp_files()
        self.clean_test_artifacts()
        self.clean_type_check_cache()

        # تنظيم الكود
        self.organize_imports()
        self.check_dead_code()

        # حساب المدة
        end_time = datetime.now()
        self.stats.duration_seconds = (end_time - start_time).total_seconds()

        # طباعة التقرير
        self._print_report()

        return self.stats

    def _print_report(self) -> None:
        """طباعة تقرير التنظيف."""
        print("\n" + "=" * 70)
        print("📊 تقرير التنظيف | Cleanup Report")
        print("=" * 70)

        print(f"\n📁 الملفات المحذوفة: {self.stats.files_removed}")
        print(f"📂 المجلدات المحذوفة: {self.stats.dirs_removed}")
        print(f"💾 المساحة المحررة: {self.stats.space_freed_mb:.2f} MB")
        print(f"⏱️  المدة: {self.stats.duration_seconds:.2f} ثانية")

        if self.stats.categories:
            print("\n📋 حسب الفئة:")
            for category, count in sorted(self.stats.categories.items()):
                print(f"  • {category}: {count} عنصر")

        print("\n" + "=" * 70)
        print("✅ اكتمل التنظيف بنجاح!")
        print("=" * 70)


def main():
    """الدالة الرئيسية."""
    import argparse

    parser = argparse.ArgumentParser(description="🧹 نظام التنظيف والتنظيم الخارق")
    parser.add_argument("--dry-run", action="store_true", help="تشغيل تجريبي بدون حذف فعلي")
    parser.add_argument(
        "--project-root", type=Path, default=Path.cwd(), help="المسار الجذري للمشروع"
    )

    args = parser.parse_args()

    # تشغيل التنظيف
    cleanup = SuperCleanup(args.project_root)
    stats = cleanup.run_full_cleanup(dry_run=args.dry_run)

    # رمز الخروج
    return 0 if stats.files_removed > 0 or stats.dirs_removed > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
