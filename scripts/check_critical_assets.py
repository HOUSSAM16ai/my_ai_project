#!/usr/bin/env python3
"""
أداة التحقق من الأصول الحيوية (Critical Assets Checker).
تستخدم هذه الأداة كـ Pre-commit Hook لمنع حذف الملفات المهمة.
"""
import sys
import os
from pathlib import Path

# قائمة الملفات الحيوية
CRITICAL_SCRIPTS = [
    "scripts/setup_dev.sh",
    "scripts/setup_pre_commit.sh",
    "scripts/start.sh",
]

def main() -> int:
    """
    الدالة الرئيسية للتحقق من وجود الملفات.
    تعيد 0 في حالة النجاح، و 1 في حالة الفشل.
    """
    root_dir = Path.cwd()
    missing_files = []

    print("🛡️  Checking critical assets integrity...")

    for script in CRITICAL_SCRIPTS:
        file_path = root_dir / script
        if not file_path.exists():
            missing_files.append(script)

    if missing_files:
        print("\n❌ CRITICAL ERROR: The following protected files are missing:")
        for f in missing_files:
            print(f"   - {f}")
        print("\n⛔ Commit blocked! Please restore these files before committing.")
        print("   Use 'git checkout <commit-hash> -- <file>' to restore.")
        return 1

    print("✅ All critical assets are present.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
