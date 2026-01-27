"""سياسات تنفيذ الأدوات وتحويل الوسائط."""

import os

from .definitions import READ_KEYWORDS, WRITE_KEYWORDS
from .globals import _TOOL_REGISTRY


def _looks_like_write(description: str) -> bool:
    """تحديد ما إذا كان وصف الأداة يشير إلى عملية كتابة."""
    lowered = description.lower()
    return any(keyword in lowered for keyword in WRITE_KEYWORDS)


def _looks_like_read(description: str) -> bool:
    """تحديد ما إذا كان وصف الأداة يشير إلى عملية قراءة."""
    lowered = description.lower()
    return any(keyword in lowered for keyword in READ_KEYWORDS)


def policy_can_execute(tool_name: str, args: dict[str, object]) -> bool:
    """تحديد ما إذا كانت السياسة تسمح بتنفيذ الأداة."""
    _ = args
    meta = _TOOL_REGISTRY.get(tool_name)
    if not meta:
        return False
    description = meta.get("description", "")
    is_write = _looks_like_write(description)
    if not is_write:
        return True
    return os.getenv("TOOL_POLICY_ALLOW_WRITE", "false").lower() == "true"


def transform_arguments(tool_name: str, args: dict[str, object]) -> dict[str, object]:
    """تحويل الوسائط قبل تمريرها للأداة مع الحفاظ على سلامة المدخلات."""
    _ = tool_name
    return args
