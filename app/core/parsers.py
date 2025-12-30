"""
وحدة تحليل النصوص (Parsers).

تحتوي هذه الوحدة على دوال لمعالجة وتحليل النصوص، خاصة تلك القادمة من نماذج الذكاء الاصطناعي (LLMs).
تتميز بالصرامة في التعامل مع الأخطاء وتوفير توثيق عربي شامل.

المعايير:
- CS50 2025: توثيق عربي، كتابة صارمة (Strict Typing).
- Robustness: التعامل مع مدخلات غير متوقعة.
"""

from typing import Any

__all__ = ["strip_markdown_fences", "extract_first_json_object"]


def strip_markdown_fences(text: str | None) -> str:
    """
    إزالة علامات Markdown (```) من النص.

    تستخدم هذه الدالة لتنظيف مخرجات نماذج اللغة التي غالبًا ما تضع الكود
    داخل كتل Markdown.

    Args:
        text (str | None): النص المدخل الذي قد يحتوي على علامات Markdown.

    Returns:
        str: النص بعد إزالة العلامات، أو نص فارغ إذا كان المدخل None.

    Example:
        >>> strip_markdown_fences("```json\\n{\\"key\\": \\"val\\"}\\n```")
        '{"key": "val"}'
    """
    if not text:
        return ""

    t = text.strip()

    # التحقق من وجود العلامات في البداية
    if t.startswith("```"):
        # البحث عن نهاية السطر الأول (اللغة)
        nl = t.find("\n")
        if nl != -1:
            t = t[nl + 1 :]

        # إزالة العلامات من النهاية
        if t.endswith("```"):
            t = t[:-3].strip()

    return t


def extract_first_json_object(text: str | None) -> str | None:
    """
    استخراج أول كائن JSON صالح من النص.

    تقوم هذه الدالة بالبحث عن أول قوس '{' وتحاول استخراج كائن JSON كامل
    عن طريق تتبع توازن الأقواس، مع تجاهل الأقواس داخل السلاسل النصية.

    Args:
        text (str | None): النص الذي يحتوي على JSON مختلط مع نصوص أخرى.

    Returns:
        str | None: كائن JSON المستخرج كسلسلة نصية، أو None إذا لم يتم العثور عليه.

    Example:
        >>> extract_first_json_object('Here is the json: {"id": 1} ...')
        '{"id": 1}'
    """
    if not text:
        return None

    # تنظيف النص أولاً من علامات Markdown
    t = strip_markdown_fences(text)

    start = t.find("{")
    if start == -1:
        return None

    # تتبع توازن الأقواس
    level = 0
    in_string = False
    escape_next = False

    for i in range(start, len(t)):
        c = t[i]

        if escape_next:
            escape_next = False
            continue

        if c == "\\":
            escape_next = True
            continue

        if c == '"' and not escape_next:
            in_string = not in_string
            continue

        if not in_string:
            if c == "{":
                level += 1
            elif c == "}":
                level -= 1
                if level == 0:
                    # تم العثور على الكائن الكامل
                    return t[start : i + 1]

    return None
