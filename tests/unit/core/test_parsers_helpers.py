"""اختبارات مساعدة لوحدة parsers للتأكد من سلامة استخراج JSON وتنظيف Markdown."""
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


def test_strip_markdown_fences_trims_language_hint() -> None:
    fenced = "```python\nprint('hi')\n```"

    assert parsers.strip_markdown_fences(fenced) == "print('hi')"


def test_remove_markdown_markers_returns_original_when_missing() -> None:
    assert parsers._remove_markdown_markers("plain text") == "plain text"


def test_extract_first_json_object_returns_none_without_braces() -> None:
    assert parsers.extract_first_json_object("no json here") is None
