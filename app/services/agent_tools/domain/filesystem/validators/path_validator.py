"""
Path validation utilities.
"""

import os
from app.services.agent_tools.utils import _safe_path

def validate_path(path: str, allow_missing: bool = False) -> str:
    """
    Validates a path using strict security boundaries.

    Args:
        path: The relative or absolute path to check.
        allow_missing: If True, does not raise if the file is missing (but checks parent dir).

    Returns:
        The resolved absolute path.

    Raises:
        ValueError: If path is unsafe or invalid.
        FileNotFoundError: If allow_missing is False and file doesn't exist.
    """
    try:
        abs_path = _safe_path(path)
    except Exception as e:
        raise ValueError(f"Invalid path security check: {e}") from e

    if not allow_missing and not os.path.exists(abs_path):
        raise FileNotFoundError(f"File not found: {path}")

    return abs_path

def validate_directory(path: str) -> str:
    """Ensures the path exists and is a directory."""
    abs_path = validate_path(path, allow_missing=False)
    if not os.path.isdir(abs_path):
        raise NotADirectoryError(f"Path is not a directory: {path}")
    return abs_path

def validate_file(path: str) -> str:
    """Ensures the path exists and is a file."""
    abs_path = validate_path(path, allow_missing=False)
    if os.path.isdir(abs_path):
        raise IsADirectoryError(f"Path is a directory: {path}")
    return abs_path
