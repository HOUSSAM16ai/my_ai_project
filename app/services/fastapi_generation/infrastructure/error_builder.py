"""
Error Message Builder - Infrastructure Layer
============================================
Builds bilingual error messages.
"""
from __future__ import annotations


class ErrorMessageBuilder:
    """Builds bilingual error messages for generation failures."""

    def build_error_message(
        self, error: str, prompt_length: int, max_tokens: int
    ) -> str:
        """
        Build bilingual error message.

        Args:
            error: Error description
            prompt_length: Length of prompt
            max_tokens: Max tokens used

        Returns:
            Formatted bilingual error message
        """
        from app.core.error_messages import build_bilingual_error_message

        return build_bilingual_error_message(error, prompt_length, max_tokens)


__all__ = ["ErrorMessageBuilder"]
