from __future__ import annotations

import logging
import os

import yaml

_LOG = logging.getLogger("yaml_utils")

class YamlSecurityError(Exception):
    """Raised when unsafe YAML loading is attempted."""

    pass

def load_yaml_safely(content: str | bytes) -> dict[str, str | int | bool]:
    """
    Safely load YAML content using yaml.safe_load().
    Strictly forbids yaml.load() to prevent Remote Code Execution (RCE).
    """
    try:
        return yaml.safe_load(content)
    except yaml.YAMLError as e:
        _LOG.error(f"Failed to parse YAML safely: {e}")
        raise YamlSecurityError(f"Invalid or unsafe YAML content: {e}") from e

def load_yaml_file_safely(path: str) -> dict[str, str | int | bool]:
    """
    Safely read and load a YAML file.
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"YAML file not found: {path}")

    with open(path, encoding="utf-8") as f:
        return load_yaml_safely(f)
