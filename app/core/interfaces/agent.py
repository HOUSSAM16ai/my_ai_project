"""
واجهة الوكيل.
-------------
تحدد هذه الواجهة عقد تنفيذ الوكلاء الحواريين بشكل واضح وقابل للاختبار.
"""

from collections.abc import AsyncGenerator
from typing import Protocol


class Agent(Protocol):
    """
    بروتوكول يحدد سلوك الوكيل الحواري.
    """

    async def run(
        self, question: str, context: dict[str, object] | None = None
    ) -> AsyncGenerator[str, None]:
        """تشغيل حلقة الوكيل وإرجاع دفعات الاستجابة."""
        ...
