from app.utils.text_processing import extract_first_json_object, strip_markdown_fences


class TestTextProcessing:
    def test_strip_markdown_fences_basic(self):
        text = "```python\nprint('hello')\n```"
        expected = "print('hello')"
        assert strip_markdown_fences(text) == expected

    def test_strip_markdown_fences_no_language(self):
        text = "```\nprint('hello')\n```"
        expected = "print('hello')"
        assert strip_markdown_fences(text) == expected

    def test_strip_markdown_fences_no_fences(self):
        text = "print('hello')"
        assert strip_markdown_fences(text) == "print('hello')"

    def test_strip_markdown_fences_empty(self):
        assert strip_markdown_fences("") == ""
        assert strip_markdown_fences(None) == ""

    def test_extract_first_json_object_basic(self):
        text = 'Some text {"key": "value"} more text'
        expected = '{"key": "value"}'
        assert extract_first_json_object(text) == expected

    def test_extract_first_json_object_nested(self):
        text = '{"outer": {"inner": "value"}}'
        expected = '{"outer": {"inner": "value"}}'
        assert extract_first_json_object(text) == expected

    def test_extract_first_json_object_with_markdown(self):
        text = '```json\n{"key": "value"}\n```'
        expected = '{"key": "value"}'
        assert extract_first_json_object(text) == expected

    def test_extract_first_json_object_none_found(self):
        assert extract_first_json_object("no json here") is None
        assert extract_first_json_object("") is None
        assert extract_first_json_object(None) is None

    def test_extract_first_json_object_incomplete(self):
        assert extract_first_json_object('{"key": "value"') is None

    def test_extract_first_json_object_with_escapes(self):
        # Escaped quotes inside string should not be counted
        text = r'{"key": "va\"lue"}'
        assert extract_first_json_object(text) == text

    def test_extract_first_json_object_with_braces_in_string(self):
        text = r'{"key": "val{ue"}'
        assert extract_first_json_object(text) == text
