from __future__ import annotations

from dataclasses import dataclass

from app.core.yaml_utils import (
    SafeYamlParser,
    YamlParser,
    YamlParserRegistry,
    load_yaml,
    load_yaml_file,
    load_yaml_file_with_selector,
    load_yaml_with_selector,
)


@dataclass
class DummyParser:
    parsed: dict[str, object] | None = None

    def parse(self, content: str | bytes) -> dict[str, object]:
        self.parsed = {"payload": content.decode() if isinstance(content, bytes) else content}
        return self.parsed


class DummySelector:
    def __init__(self, parser: YamlParser) -> None:
        self._parser = parser

    def resolve(self, _name: str | None = None) -> YamlParser:
        return self._parser


def test_load_yaml_with_injected_parser() -> None:
    parser = DummyParser()
    result = load_yaml("key: value", parser=parser)

    assert result == {"payload": "key: value"}
    assert parser.parsed == {"payload": "key: value"}


def test_load_yaml_with_selector_interface() -> None:
    parser = DummyParser()
    selector = DummySelector(parser)

    result = load_yaml_with_selector("foo: bar", selector)

    assert result == {"payload": "foo: bar"}


def test_load_yaml_file_with_selector(tmp_path) -> None:
    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text("key: value", encoding="utf-8")

    parser = DummyParser()
    selector = DummySelector(parser)

    result = load_yaml_file_with_selector(str(yaml_file), selector)

    assert result == {"payload": "key: value"}


def test_safe_yaml_parser_passes_through_dict() -> None:
    parser = SafeYamlParser()
    result = parser.parse("key: value")

    assert result == {"key": "value"}


def test_yaml_parser_registry_resolves_default() -> None:
    registry = YamlParserRegistry(SafeYamlParser())

    resolved = registry.resolve("missing")

    assert isinstance(resolved, SafeYamlParser)


def test_registry_can_act_as_selector() -> None:
    registry = YamlParserRegistry(SafeYamlParser())

    result = load_yaml_with_selector("key: value", registry)

    assert result == {"key": "value"}


def test_load_yaml_file_uses_injected_parser(tmp_path) -> None:
    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text("key: value", encoding="utf-8")

    parser = DummyParser()

    result = load_yaml_file(str(yaml_file), parser=parser)

    assert result == {"payload": "key: value"}
