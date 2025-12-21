"""
Security utilities for chat.
"""

import re


class PathValidator:
    """Validate file paths."""

    @staticmethod
    def validate(path: str) -> bool:
        """Validate path is safe."""
        # Prevent traversal
        if ".." in path:
            return False
        # Prevent absolute paths (optional, depending on requirements)
        return not path.startswith("/")


class ErrorSanitizer:
    """Sanitize error messages."""

    @staticmethod
    def sanitize(error: Exception) -> str:
        """Sanitize error message."""
        msg = str(error)
        # Remove potential secrets or paths
        msg = re.sub(r"/.+/", "...", msg)
        return msg
