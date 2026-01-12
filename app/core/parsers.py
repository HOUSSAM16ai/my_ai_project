"""
وحدة تحليل النصوص (Parsers).

تحتوي هذه الوحدة على دوال لمعالجة وتحليل النصوص، خاصة تلك القادمة من نماذج الذكاء الاصطناعي (LLMs).
تتميز بالصرامة في التعامل مع الأخطاء وتوفير توثيق عربي شامل.

المعايير:
- CS50 2025: توثيق عربي، كتابة صارمة (Strict Typing).
- Robustness: التعامل مع مدخلات غير متوقعة.
"""

__all__ = ["extract_first_json_object", "strip_markdown_fences"]


def strip_markdown_fences(text: str | None) -> str:
    """
    إزالة علامات Markdown (```) من النص.

    تستخدم هذه الدالة لتنظيف مخرجات نماذج اللغة التي غالبًا ما تضع الكود
    داخل كتل Markdown.

    Args:
        text (str | None): النص المدخل الذي قد يحتوي على علامات Markdown.

    Returns:
        str: النص بعد إزالة العلامات، أو نص فارغ إذا كان المدخل None.
    """
    if not text:
        return ""

    t = text.strip()
    return _remove_markdown_markers(t)


def _remove_markdown_markers(text: str) -> str:
    """
    إزالة علامات Markdown من بداية ونهاية النص.
    """
    if not text.startswith("```"):
        return text

    # Remove opening block
    nl = text.find("\n")
    if nl != -1:
        text = text[nl + 1 :]

    # Remove closing block
    if text.endswith("```"):
        text = text[:-3].strip()

    return text


def extract_first_json_object(text: str | None) -> str | None:
    """
    استخراج أول كائن JSON صالح من النص.

    تقوم هذه الدالة بالبحث عن أول قوس '{' وتحاول استخراج كائن JSON كامل
    عن طريق تتبع توازن الأقواس، مع تجاهل الأقواس داخل السلاسل النصية.

    Args:
        text (str | None): النص الذي يحتوي على JSON مختلط مع نصوص أخرى.

    Returns:
        str | None: كائن JSON المستخرج كسلسلة نصية، أو None إذا لم يتم العثور عليه.
    """
    if not text:
        return None

    # تنظيف النص أولاً من علامات Markdown
    t = strip_markdown_fences(text)

    start_index = t.find("{")
    if start_index == -1:
        return None

    return _find_balanced_json_block(t, start_index)


def _find_balanced_json_block(text: str, start_index: int) -> str | None:
    """
    العثور على كتلة JSON متوازنة الأقواس بدءاً من مؤشر معين.
    """
    level = 0
    in_string = False
    escape_next = False

    for i in range(start_index, len(text)):
        char = text[i]

        if escape_next:
            escape_next = False
            continue

        if char == "\\":
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if not in_string:
            if char == "{":
                level += 1
            elif char == "}":
                level -= 1
                if level == 0:
                    return text[start_index : i + 1]

    return None
