"""وحدة YAML خفيفة وآمنة مدمجة داخل المستودع.

توفر هذه الوحدة بديلاً بسيطاً لمكتبة PyYAML عندما لا تكون متاحة في بيئات CI
المحدودة بالشبكة. يتم التركيز على التحميل الآمن فقط، مع دعم مجموعة جزئية من
تركيب YAML تكفي لاختبارات الأمان والملفات البسيطة ضمن المشروع.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class YAMLError(Exception):
    """استثناء عام لأخطاء معالجة YAML."""


class ConstructorError(YAMLError):
    """يُطلق عند اكتشاف علامات غير آمنة مثل !!python."""


@dataclass
class _ConstructorNamespace:
    """مساحة أسماء تحاكي yaml.constructor المستخدمة في PyYAML."""

    ConstructorError: type[ConstructorError]


constructor = _ConstructorNamespace(ConstructorError=ConstructorError)


def safe_load(stream: str | bytes | Any) -> Any:
    """تحميل YAML بشكل آمن مع رفض العلامات غير الموثوقة.

    يقبل نصاً، بايتات، أو كائناً يدعم ``read`` مثل الملفات.
    يتم دعم القواميس والقوائم والقيم الأساسية فقط. أي محاولة لاستخدام
    علامات مخصّصة أو بناءات غير مسموح بها تؤدي لرفع ``ConstructorError``.
    """

    text = _coerce_to_text(stream)

    if "!!" in text:
        raise ConstructorError("Unsafe YAML tag detected")

    try:
        parsed, index = _parse_block(_split_clean_lines(text), 0)
        # تجاهل الأسطر الفارغة المتبقية إن وجدت
        return parsed
    except ConstructorError:
        raise
    except Exception as exc:  # pragma: no cover - تحويل الأخطاء لواجهة موحّدة
        raise YAMLError(str(exc)) from exc


# واجهة مساندة لملاءمة API PyYAML
safe_load_all = safe_load


def _coerce_to_text(stream: str | bytes | Any) -> str:
    if hasattr(stream, "read"):
        stream = stream.read()
    if isinstance(stream, bytes):
        return stream.decode()
    if isinstance(stream, str):
        return stream
    raise YAMLError("Unsupported stream type")


def _split_clean_lines(text: str) -> list[str]:
    raw_lines = [line.rstrip("\n") for line in text.splitlines() if line.strip()]
    if not raw_lines:
        return []

    min_indent = min(_indent_of(line) for line in raw_lines if line.strip())
    return [line[min_indent:] if len(line) >= min_indent else line for line in raw_lines]


def _parse_block(lines: list[str], start: int, indent: int = 0) -> tuple[Any, int]:
    if start >= len(lines):
        return {}, start

    current_indent = _indent_of(lines[start])
    if lines[start].lstrip().startswith("- "):
        return _parse_list(lines, start, indent)
    if current_indent != indent:
        raise YAMLError("Invalid indentation")
    return _parse_mapping(lines, start, indent)


def _parse_list(lines: list[str], start: int, indent: int) -> tuple[list[Any], int]:
    items: list[Any] = []
    index = start
    while index < len(lines):
        line = lines[index]
        if _indent_of(line) < indent or not line.lstrip().startswith("- "):
            break
        value_part = line.lstrip()[2:].strip()
        if value_part:
            items.append(_parse_scalar(value_part))
            index += 1
            continue
        # عنصر ذو كتلة فرعية
        index += 1
        nested, index = _parse_block(lines, index, indent + 2)
        items.append(nested)
    return items, index


def _parse_mapping(lines: list[str], start: int, indent: int) -> tuple[dict[str, Any], int]:
    mapping: dict[str, Any] = {}
    index = start
    while index < len(lines):
        line = lines[index]
        current_indent = _indent_of(line)
        if current_indent < indent:
            break
        if current_indent != indent:
            raise YAMLError("Misaligned indentation in mapping")

        if ":" not in line:
            raise YAMLError(f"Invalid mapping line: {line}")

        key, _, rest = line.strip().partition(":")
        value_text = rest.strip()

        index += 1
        if value_text:
            mapping[key] = _parse_scalar(value_text)
            continue

        if index >= len(lines):
            mapping[key] = None
            break

        nested_indent = indent + 2
        if _indent_of(lines[index]) < nested_indent:
            mapping[key] = None
            continue

        nested, index = _parse_block(lines, index, nested_indent)
        mapping[key] = nested
    return mapping, index


def _parse_scalar(text: str) -> Any:
    lowered = text.lower()
    if lowered in {"true", "yes"}:
        return True
    if lowered in {"false", "no"}:
        return False
    if lowered in {"null", "none"}:
        return None

    try:
        return int(text)
    except ValueError:
        try:
            return float(text)
        except ValueError:
            pass

    if (text.startswith("\"") and text.endswith("\"")) or (text.startswith("'") and text.endswith("'")):
        return text[1:-1]

    return text


def _indent_of(line: str) -> int:
    return len(line) - len(line.lstrip(" "))
