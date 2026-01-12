"""
بديل مبسط لحزمة redis لتسهيل الاختبارات في البيئات التي لا تحتوي على redis-py.
"""

from redis import asyncio  # noqa: F401
