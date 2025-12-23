"""
محرك قاعدة البيانات (Database Engine) - قلب البيانات.

هذا الملف هو المسؤول الوحيد عن إنشاء وإدارة الاتصال بقاعدة البيانات في النظام.
تم تبسيطه ليكون مفهوماً للمطورين المبتدئين، مع الالتزام بمبادئ Clean Code.

المبادئ (Principles):
- SRP: مسؤول فقط عن الاتصال وإنشاء الجلسات.
- KISS: تم نقل التعقيدات (التحقق من المخطط، التوافق القديم) إلى ملفات منفصلة.
- Async First: النظام مصمم ليعمل بشكل غير متزامن للحصول على أعلى أداء.
"""

import logging
from collections.abc import AsyncGenerator
from typing import Final

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.engine_factory import create_unified_async_engine

logger = logging.getLogger(__name__)

__all__ = [
    "async_session_factory",
    "engine",
    "get_db",
]


# 1. إنشاء المحرك (The Engine)
# المحرك هو المسؤول عن الاتصال الفعلي بقاعدة البيانات.
# نستخدم دالة مصنع (Factory Function) لضمان توحيد الإعدادات.
engine: Final[AsyncEngine] = create_unified_async_engine()


# 2. مصنع الجلسات (Session Factory)
# هذا المصنع يقوم بإنشاء "جلسات" (Sessions) للتفاعل مع قاعدة البيانات.
# كل طلب (Request) يحصل على جلسة خاصة به.
async_session_factory: Final[async_sessionmaker[AsyncSession]] = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # الحفاظ على البيانات بعد الحفظ لتقليل الاستعلامات
    autocommit=False,        # نحن نتحكم متى يتم الحفظ (Commit) يدوياً للأمان
    autoflush=False,         # تأجيل إرسال البيانات للقاعدة حتى اللحظة الأخيرة
)


# 3. حاقن التبعية (Dependency Injection)
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    مزود جلسات قاعدة البيانات (Database Session Provider).

    يستخدم هذا التابع في موجهات FastAPI (Routers) للحصول على اتصال آمن بقاعدة البيانات.
    يضمن هذا التابع:
    1. فتح الجلسة عند بدء الطلب.
    2. إغلاق الجلسة تلقائياً عند انتهاء الطلب (حتى لو حدث خطأ).
    3. التراجع عن التغييرات (Rollback) في حال حدوث خطأ.

    مثال للاستخدام:
        @router.get("/")
        async def read_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_factory() as session:
        try:
            yield session
        except Exception as e:
            # تسجيل الخطأ والتراجع عن التغييرات لحماية البيانات
            logger.error(f"❌ Database session error: {e!s}")
            await session.rollback()
            raise
        finally:
            # ضمان إغلاق الجلسة دائماً لتحرير الموارد
            await session.close()
