
import pytest
from unittest.mock import patch, mock_open
from app.core import yaml_utils

def test_safe_yaml_parser_valid():
    parser = yaml_utils.SafeYamlParser()
    content = "key: value"
    result = parser.parse(content)
    assert result == {"key": "value"}

def test_safe_yaml_parser_invalid():
    parser = yaml_utils.SafeYamlParser()
    content = ": invalid"
    with pytest.raises(yaml_utils.YamlSecurityError):
        parser.parse(content)

def test_yaml_string_source():
    content = "data: 123"
    source = yaml_utils.YamlStringSource(content)
    assert source.read() == content

def test_yaml_file_source_success():
    path = "test.yaml"
    content = "foo: bar"
    with patch("builtins.open", mock_open(read_data=content)):
        with patch("os.path.exists", return_value=True):
            source = yaml_utils.YamlFileSource(path)
            assert source.read() == content

def test_yaml_file_source_not_found():
    path = "missing.yaml"
    with patch("os.path.exists", return_value=False):
        source = yaml_utils.YamlFileSource(path)
        with pytest.raises(FileNotFoundError):
            source.read()

def test_yaml_loader():
    source = yaml_utils.YamlStringSource("item: test")
    parser = yaml_utils.SafeYamlParser()
    loader = yaml_utils.YamlLoader(source, parser)
    result = loader.load()
    assert result == {"item": "test"}

def test_load_yaml_safely():
    content = "safe: true"
    result = yaml_utils.load_yaml_safely(content)
    assert result == {"safe": True}

def test_yaml_parser_registry():
    default = yaml_utils.SafeYamlParser()
    registry = yaml_utils.YamlParserRegistry(default)
    
    assert registry.resolve() == default
    assert registry.resolve("unknown") == default
    
    # Register mock parser
    mock_parser = yaml_utils.SafeYamlParser() # structurally same
    registry.register("custom", mock_parser)
    assert registry.resolve("custom") == mock_parser
