"""اختبارات مساعدة لوحدة parsers لضمان سلامة استخراج JSON وتنظيف Markdown."""
from app.core import parsers

def test_strip_markdown_fences_removes_code_block() -> None:
    content = "```json\n{\n  \"value\": 42\n}\n```"

    cleaned = parsers.strip_markdown_fences(content)

    assert cleaned == '{\n  "value": 42\n}'


def test_strip_markdown_fences_handles_plain_text_and_none() -> None:
    assert parsers.strip_markdown_fences("no markers") == "no markers"
    assert parsers.strip_markdown_fences(None) == ""


def test_find_balanced_json_block_ignores_braces_inside_strings() -> None:
    text = 'preface {"message": "keep { inside text }", "status": "ok"} trailing'
    start = text.find("{")

    result = parsers._find_balanced_json_block(text, start)

    assert result == '{"message": "keep { inside text }", "status": "ok"}'


def test_extract_first_json_object_removes_markdown_before_parsing() -> None:
    text = (
        "metadata before\n"
        "```json\n"
        "{\"outer\": {\"inner\": 1}}\n"
        "```\n"
        "footer"
    )

    extracted = parsers.extract_first_json_object(text)

    assert extracted == '{"outer": {"inner": 1}}'


def test_find_balanced_json_block_returns_none_when_unbalanced() -> None:
    text = '{"incomplete": true'

    assert parsers._find_balanced_json_block(text, 0) is None


def test_find_balanced_json_block_handles_nested_objects() -> None:
    text = "prefix {\"outer\": {\"inner\": {\"deep\": true}}} suffix"
    start = text.find("{")

    result = parsers._find_balanced_json_block(text, start)

    assert result == '{"outer": {"inner": {"deep": true}}}'


def test_strip_markdown_fences_trims_language_hint() -> None:
    fenced = "```python\nprint('hi')\n```"

    assert parsers.strip_markdown_fences(fenced) == "print('hi')"


def test_remove_markdown_markers_returns_original_when_missing() -> None:
    assert parsers._remove_markdown_markers("plain text") == "plain text"


def test_extract_first_json_object_returns_none_without_braces() -> None:
    assert parsers.extract_first_json_object("no json here") is None


def test_find_balanced_json_block_handles_escaped_quotes() -> None:
    text = '{"message": "line with \"escaped quotes\"", "flag": true}'

    result = parsers._find_balanced_json_block(text, 0)

    assert result == text


def test_strip_markdown_fences_trims_whitespace_after_markers() -> None:
    fenced = "```\n{\n  \"ok\": true\n}\n```   \n"

    assert parsers.strip_markdown_fences(fenced) == '{\n  "ok": true\n}'


def test_strip_markdown_fences_handles_missing_closing_marker() -> None:
    text = "```json\n{\"value\": 1}"

    assert parsers.strip_markdown_fences(text) == '{"value": 1}'


def test_remove_markdown_markers_strips_language_and_padding() -> None:
    text = "```python\nprint('hi')\n```"

    assert parsers._remove_markdown_markers(text) == "print('hi')"


def test_find_balanced_json_block_handles_escaped_backslashes() -> None:
    text = '{"message": "path \\\\server\\share", "ok": true} trailing data'

    assert parsers._find_balanced_json_block(text, 0) == '{"message": "path \\\\server\\share", "ok": true}'
