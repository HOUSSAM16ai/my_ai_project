"""
وحدة اختبار الأصول الحيوية للبنية التحتية.
تتحقق هذه الوحدة من وجود وسلامة الملفات النصية (scripts) المهمة لبيئة التطوير والتشغيل.
"""

import os
import stat
from pathlib import Path
import pytest

# قائمة الملفات الحيوية التي يجب حمايتها
CRITICAL_SCRIPTS: list[str] = [
    "scripts/setup_dev.sh",
    "scripts/setup_pre_commit.sh",
    "scripts/start.sh",
]

def test_critical_scripts_exist() -> None:
    """
    اختبار وجود السكريبتات الحيوية.

    يتحقق هذا الاختبار من أن جميع الملفات المدرجة في القائمة `CRITICAL_SCRIPTS`
    موجودة فعليًا في نظام الملفات. هذا يمنع الحذف العرضي للملفات المهمة.
    """
    missing_scripts: list[str] = []

    for script_path in CRITICAL_SCRIPTS:
        path = Path(script_path)
        if not path.exists():
            missing_scripts.append(script_path)

    assert not missing_scripts, f"الملفات الحيوية التالية مفقودة: {', '.join(missing_scripts)}"

def test_critical_scripts_executable() -> None:
    """
    اختبار قابلية تنفيذ السكريبتات الحيوية.

    يتحقق هذا الاختبار من أن الملفات الموجودة تمتلك صلاحيات التنفيذ (+x).
    هذا ضروري لضمان عمل بيئة التطوير والتشغيل بشكل صحيح.
    """
    non_executable_scripts: list[str] = []

    for script_path in CRITICAL_SCRIPTS:
        path = Path(script_path)
        if path.exists():
            # التحقق من صلاحيات التنفيذ
            is_executable = os.access(path, os.X_OK)
            # بديل للتحقق من الـ bit مباشرة في أنظمة Unix
            st = os.stat(path)
            has_exec_bit = bool(st.st_mode & stat.S_IEXEC)

            if not (is_executable or has_exec_bit):
                non_executable_scripts.append(script_path)

    assert not non_executable_scripts, f"الملفات التالية ليست قابلة للتنفيذ: {', '.join(non_executable_scripts)}"
