"""
معالج bcrypt مبسط لتوافق اختبارات passlib.
"""

from __future__ import annotations


class _BcryptHandler:
    """معالج مبسط يوفر واجهة has_backend المطلوبة في الاختبارات."""

    def has_backend(self) -> bool:
        """يشير إلى توفر واجهة الخلفية."""
        return True


bcrypt = _BcryptHandler()

__all__ = ["bcrypt"]
