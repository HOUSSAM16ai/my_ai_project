"""
تعريفات البيانات المشتركة لخدمة المصادقة.
"""

from typing import TypedDict


class TokenBundle(TypedDict):
    """تمثيل منظم لحزمة الرموز المصدرة."""

    access_token: str
    refresh_token: str
    token_type: str
