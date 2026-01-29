"""نماذج تنفيذ الأدوات وسياقاتها."""

from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class ToolExecutionContext:
    """يمثل هذا الصنف سياق تنفيذ الأداة بما يحمله من إعدادات ومعطيات تشغيل."""

    name: str
    trace_id: str
    meta_entry: dict[str, object]
    func: Callable[..., object]
    kwargs: dict[str, object]


@dataclass
class ToolExecutionInfo:
    """يحمل هذا الصنف معلومات التتبع والقياس الخاصة بتنفيذ الأداة."""

    reg_name: str
    canonical_name: str
    elapsed_ms: float
    category: str
    capabilities: list[str]
    meta_entry: dict[str, object]
    trace_id: str
