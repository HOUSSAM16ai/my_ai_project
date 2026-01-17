"""
واجهة Redis غير متزامنة مبسطة للاختبارات.

هذه الواجهة تسمح باستيراد `redis.asyncio` داخل الاختبارات دون
الحاجة إلى تثبيت الاعتماد الخارجي.
"""


def from_url(*_args: object, **_kwargs: object) -> object:
    """
    إنشاء عميل Redis وهمي (سيتم استبداله بالـ mocks في الاختبارات).
    """
    raise RuntimeError("redis.asyncio.from_url stub should be mocked in tests.")

