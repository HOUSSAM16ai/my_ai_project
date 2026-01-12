"""
اختبارات مبادئ النظام الصارمة.
"""

import pytest

from app.core.agents.system_principles import (
    SystemPrinciple,
    format_system_principles,
    validate_system_principles,
)


def test_validate_system_principles_accepts_default_catalog() -> None:
    """اختبار: التحقق يمر بنجاح على القائمة الرسمية."""
    validate_system_principles()


def test_validate_system_principles_rejects_invalid_numbers() -> None:
    """اختبار: التحقق يرفض الترقيم غير المكتمل أو المكرر."""
    invalid = (
        SystemPrinciple(1, "مبدأ أول."),
        SystemPrinciple(1, "مبدأ مكرر."),
    )

    with pytest.raises(ValueError, match="ترقيم مبادئ النظام"):
        validate_system_principles(invalid)


def test_format_system_principles_includes_first_item() -> None:
    """اختبار: التنسيق يتضمن العنصر الأول بشكل واضح."""
    formatted = format_system_principles()

    assert "1." in formatted
