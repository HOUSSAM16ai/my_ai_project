"""
Text Processing Utilities
=========================

Common text processing functions extracted to eliminate code duplication.
These utilities are used across multiple services for consistent text handling.
"""


def strip_markdown_fences(text: str) -> str:
    """
    Remove markdown code fences (```) from text.

    This function handles markdown code blocks by removing the opening and closing
    backtick fences, commonly used when LLMs wrap code in markdown format.

    Args:
        text: Input text that may contain markdown fences

    Returns:
        Text with markdown fences removed

    Example:
        >>> strip_markdown_fences("```python\\nprint('hello')\\n```")
        "print('hello')"
    """
    if not text:
        return ""
    t = text.strip()
    if t.startswith("```"):
        nl = t.find("\n")
        if nl != -1:
            t = t[nl + 1 :]
        if t.endswith("```"):
            t = t[:-3].strip()
    return t


def extract_first_json_object(text: str) -> str | None:
    """
    Extract the first JSON object from text using balanced brace matching.

    This naive implementation finds the first '{' and attempts to extract
    a complete JSON object by tracking brace balance. Useful for parsing
    LLM responses that may contain JSON mixed with other text.

    Args:
        text: Input text that may contain JSON objects

    Returns:
        First JSON object as string, or None if not found

    Example:
        >>> extract_first_json_object('Some text {"key": "value"} more text')
        '{"key": "value"}'
    """
    if not text:
        return None

    # Strip markdown fences first
    t = strip_markdown_fences(text)

    start = t.find("{")
    if start == -1:
        return None

    # Track brace balance
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
                    return t[start : i + 1]

    return None
