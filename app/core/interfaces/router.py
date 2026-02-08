"""
واجهة موجه المقاصد (ISP).
-------------------------
تحدد عقد توجيه المقاصد إلى المعالجات المناسبة.
"""

from collections.abc import AsyncGenerator
from typing import Protocol


class IntentRouter(Protocol):
    """
    بروتوكول لتحديد المقصد الصحيح وتنفيذه.
    """

    async def route_and_execute(
        self, question: str, context: dict[str, object] | None = None
    ) -> AsyncGenerator[str, None]:
        """
        تحليل السؤال والسياق، وتوجيه الطلب إلى المعالج المناسب،
        ثم بث أجزاء الاستجابة تدريجيًا.
        """
        ...
