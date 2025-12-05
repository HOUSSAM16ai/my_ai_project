from __future__ import annotations

import re
from typing import ClassVar


class PathValidator:
    """Validates file paths to prevent traversal attacks."""

    BLOCKED_PATTERNS: ClassVar[list[str]] = [
        r"\.\./",
        r"\.\.\\",
        r"^/",
        r"^[A-Za-z]:",
        r"~",
        r"\x00",
    ]

    ALLOWED_EXTENSIONS: ClassVar[set[str]] = {
        ".py",
        ".md",
        ".txt",
        ".json",
        ".yaml",
        ".yml",
        ".js",
        ".ts",
        ".html",
        ".css",
        ".sh",
        ".sql",
        ".toml",
        ".cfg",
        ".ini",
        ".env.example",
    }

    @classmethod
    def validate(cls, path: str) -> tuple[bool, str]:
        """Validate a file path."""
        if not path or len(path) > 500:
            return False, "Invalid path length"

        for pattern in cls.BLOCKED_PATTERNS:
            if re.search(pattern, path):
                return False, "Path contains blocked pattern"

        from pathlib import Path

        path_obj = Path(path)
        suffixes = path_obj.suffixes
        if suffixes:
            ext = suffixes[-1].lower()
            full_ext = "".join(s.lower() for s in suffixes)
            if ext not in cls.ALLOWED_EXTENSIONS and full_ext not in cls.ALLOWED_EXTENSIONS:
                return False, f"Extension not allowed: {ext}"

        return True, "ok"


class ErrorSanitizer:
    """Sanitizes error messages to prevent information leakage."""

    PATTERNS_TO_REMOVE: ClassVar[list[tuple[str, str]]] = [
        (r"/[a-zA-Z0-9_/.-]+\.py", "[file]"),
        (r"line \d+", "line [N]"),
        (r"at 0x[a-fA-F0-9]+", "at [addr]"),
        (r"password['\"]?\s*[:=]\s*['\"]?[^'\"]+['\"]?", "password=[REDACTED]"),
        (r"api[_-]?key['\"]?\s*[:=]\s*['\"]?[^'\"]+['\"]?", "api_key=[REDACTED]"),
    ]

    @classmethod
    def sanitize(cls, error: str | None, max_length: int = 200) -> str:
        """Sanitize an error message."""
        if not error:
            return "Unknown error"

        result = str(error)
        for pattern, replacement in cls.PATTERNS_TO_REMOVE:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)

        if len(result) > max_length:
            result = result[:max_length] + "..."
        return result
