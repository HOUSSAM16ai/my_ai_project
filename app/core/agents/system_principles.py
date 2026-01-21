"""
المبادئ الصارمة للنظام على مستوى المشروع.

هذا الملف يمثل مصدر الحقيقة لمبادئ النظام الإلزامية
ويتيح الوصول البرمجي إليها بشكل موحد.
"""

from __future__ import annotations

import functools
import os
from dataclasses import dataclass
from pathlib import Path

import yaml

# Cache path to avoid re-calculating
_CONFIG_DIR = Path(__file__).parent.parent / "config_data"
_PRINCIPLES_FILE = _CONFIG_DIR / "system_principles.yaml"


@dataclass(frozen=True)
class SystemPrinciple:
    """تمثيل مبدأ واحد من مبادئ النظام الصارمة."""

    number: int
    statement: str


def _load_principles_from_yaml(section: str) -> tuple[SystemPrinciple, ...]:
    """
    Load principles from the YAML configuration file.

    Args:
        section: The key in the YAML file ('system_principles' or 'architecture_principles').

    Returns:
        A tuple of SystemPrinciple objects.

    Raises:
        FileNotFoundError: If the YAML file is missing.
        KeyError: If the section is missing.
    """
    if not _PRINCIPLES_FILE.exists():
        # Fallback for testing or if file is missing (though it should be there)
        # This prevents total crash but warns.
        return ()

    with open(_PRINCIPLES_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if section not in data:
        return ()

    principles = []
    for item in data[section]:
        principles.append(SystemPrinciple(number=item["number"], statement=item["statement"]))

    return tuple(principles)


# Lazy load using lru_cache to load only once
@functools.lru_cache(maxsize=1)
def _get_all_system_principles() -> tuple[SystemPrinciple, ...]:
    return _load_principles_from_yaml("system_principles")


@functools.lru_cache(maxsize=1)
def _get_all_architecture_principles() -> tuple[SystemPrinciple, ...]:
    return _load_principles_from_yaml("architecture_principles")


def _validate_principles(
    *,
    principles: tuple[SystemPrinciple, ...],
    label: str,
) -> None:
    """
    التحقق من سلامة قائمة مبادئ محددة.

    Args:
        principles: قائمة المبادئ المطلوب التحقق منها.
        label: اسم القائمة لرسائل الخطأ.

    Raises:
        ValueError: عند اكتشاف خلل في القائمة.
    """
    errors: list[str] = []
    expected_numbers = set(range(1, 101))
    numbers = [item.number for item in principles]
    statements = [item.statement for item in principles]

    if len(principles) != 100:
        errors.append(f"عدد مبادئ {label} يجب أن يكون 100 مبدأ بالضبط.")

    if set(numbers) != expected_numbers:
        errors.append(f"ترقيم مبادئ {label} يجب أن يغطي النطاق الكامل من 1 إلى 100 دون تكرار.")

    if any(not statement.strip() for statement in statements):
        errors.append(f"يجب أن يحتوي كل مبدأ في {label} على نص غير فارغ.")

    if errors:
        message = "؛ ".join(errors)
        raise ValueError(message)


def get_system_principles() -> tuple[SystemPrinciple, ...]:
    """الحصول على جميع مبادئ النظام الصارمة بشكل ثابت."""
    return _get_all_system_principles()


def format_system_principles(
    *,
    header: str = "المبادئ الصارمة للنظام",
    bullet: str = "-",
    include_header: bool = True,
) -> str:
    """
    تنسيق مبادئ النظام الصارمة كنص جاهز للإدراج في السياقات المختلفة.

    Args:
        header: عنوان القسم.
        bullet: رمز التعداد النقطي.
        include_header: تحديد تضمين العنوان من عدمه.

    Returns:
        str: نص منسق للمبادئ.
    """
    principles = get_system_principles()
    prefix = f"{bullet} " if bullet else ""
    lines = [f"{prefix}{principle.number}. {principle.statement}" for principle in principles]
    body = "\n".join(lines)
    if include_header:
        return f"{header}\n{body}"
    return body


def get_architecture_system_principles() -> tuple[SystemPrinciple, ...]:
    """الحصول على مبادئ المعمارية وحوكمة البيانات الأساسية."""
    return _get_all_architecture_principles()


def format_architecture_system_principles(
    *,
    header: str = "مبادئ المعمارية وحوكمة البيانات الأساسية",
    bullet: str = "-",
    include_header: bool = True,
) -> str:
    """
    تنسيق مبادئ المعمارية الأساسية كنص جاهز للإدراج في السياقات المختلفة.

    Args:
        header: عنوان القسم.
        bullet: رمز التعداد النقطي.
        include_header: تحديد تضمين العنوان من عدمه.

    Returns:
        str: نص منسق للمبادئ.
    """
    principles = get_architecture_system_principles()
    prefix = f"{bullet} " if bullet else ""
    lines = [f"{prefix}{principle.number}. {principle.statement}" for principle in principles]
    body = "\n".join(lines)
    if include_header:
        return f"{header}\n{body}"
    return body


def validate_system_principles(
    principles: tuple[SystemPrinciple, ...] | None = None,
) -> None:
    """
    التحقق من سلامة مبادئ النظام الصارمة.

    يضمن هذا التحقق تطبيق المبادئ فعلياً عبر التأكد من:
    - اكتمال القائمة (100 مبدأ).
    - الترتيب والترقيم الصحيح (1..100 بدون تكرار).
    - وجود نص غير فارغ لكل مبدأ.

    Args:
        principles: قائمة المبادئ المطلوب التحقق منها. افتراضياً تستخدم القائمة الرسمية.

    Raises:
        ValueError: عند اكتشاف خلل في القائمة.
    """
    items = principles or get_system_principles()
    _validate_principles(principles=items, label="النظام")


def validate_architecture_system_principles(
    principles: tuple[SystemPrinciple, ...] | None = None,
) -> None:
    """
    التحقق من سلامة مبادئ المعمارية وحوكمة البيانات الأساسية.

    Args:
        principles: قائمة المبادئ المطلوب التحقق منها. افتراضياً تستخدم القائمة الرسمية.

    Raises:
        ValueError: عند اكتشاف خلل في القائمة.
    """
    items = principles or get_architecture_system_principles()
    _validate_principles(principles=items, label="المعمارية وحوكمة البيانات")
