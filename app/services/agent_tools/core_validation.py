"""التحقق من مدخلات الأدوات وفق مخطط المعلمات."""

from .definitions import SUPPORTED_TYPES


def _validate_type(name: str, value: dict[str, str | int | bool], expected: str) -> None:
    """التحقق من نوع قيمة الحقل وفق نوعه المتوقع."""
    py_type = SUPPORTED_TYPES.get(expected)
    if py_type and not isinstance(value, py_type):
        raise TypeError(f"Parameter '{name}' must be of type '{expected}'.")


def _validate_arguments(schema: dict[str, object], args: dict[str, object]) -> dict[str, object]:
    """تطبيق قواعد المخطط على الوسائط وإرجاع نسخة منقحة."""
    if not isinstance(schema, dict) or schema.get("type") != "object":
        return args
    properties = schema.get("properties", {}) or {}
    required = schema.get("required", []) or []
    cleaned: dict[str, object] = {}
    for field, meta in properties.items():
        if field in args:
            value = args[field]
        elif "default" in meta:
            value = meta["default"]
        else:
            continue
        et = meta.get("type")
        if et in SUPPORTED_TYPES:
            _validate_type(field, value, et)
        cleaned[field] = value
    missing = [r for r in required if r not in cleaned]
    if missing:
        raise ValueError(f"Missing required parameters: {missing}")
    return cleaned
