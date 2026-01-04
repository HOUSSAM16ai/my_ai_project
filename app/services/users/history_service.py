"""
خدمة سجل المحادثات (History Service).

هذه الخدمة مسؤولة عن استرجاع وإدارة سجلات المحادثات وتقييمات الرسائل.
تم تحديثها لتدعم العمليات غير المتزامنة (Async) بالكامل باستخدام SQLAlchemy Async.
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from sqlalchemy import exc as sqlalchemy_exc
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import async_session_factory

if TYPE_CHECKING:
    from app.core.domain.models import AdminConversation, AdminMessage

logger = logging.getLogger(__name__)


async def get_recent_conversations(user_id: int, limit: int = 5) -> list[AdminConversation]:
    """
    استرجاع أحدث المحادثات للمستخدم الحالي.

    هذه دالة لاسترجاع البيانات فقط (Pure Retrieval) باستخدام جلسة قاعدة بيانات غير متزامنة.

    Args:
        user_id: معرف المستخدم الذي سيتم استرجاع محادثاته.
        limit: الحد الأقصى لعدد المحادثات المسترجعة (الافتراضي: 5).

    Returns:
        list[AdminConversation]: قائمة كائنات المحادثات، أو قائمة فارغة في حال حدوث خطأ.
    """
    # استيراد النماذج داخل الدالة لتجنب التبعيات الدائرية (Lazy Import)
    from app.core.domain.models import AdminConversation as Conversation

    try:
        async with async_session_factory() as session:
            stmt = (
                select(Conversation)
                .where(Conversation.user_id == user_id)
                .order_by(Conversation.created_at.desc(), Conversation.id.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            conversations = result.scalars().all()
            return list(conversations)
    except Exception as e:
        logger.error(
            f"فشل في استرجاع المحادثات الأخيرة للمستخدم {user_id}: {e}", exc_info=True
        )
        return []


async def rate_message_in_db(
    message_id: int, rating: str, user_id: int
) -> dict[str, object]:
    """
    تقييم رسالة محددة في قاعدة البيانات.

    تعتبر هذه الدالة النواة الأساسية لحلقة التغذية الراجعة (Feedback Loop) لتعلم الذكاء الاصطناعي.

    Args:
        message_id: معرف الرسالة المراد تقييمها.
        rating: قيمة التقييم ('good', 'bad', أو 'neutral').
        user_id: معرف المستخدم الذي يقوم بالتقييم (لأغراض الأمان والتحقق من الملكية).

    Returns:
        dict[str, object]: قاموس يحتوي على حالة العملية والرسالة الوصفية.
    """
    from app.core.domain.models import AdminMessage as Message

    if rating not in ["good", "bad", "neutral"]:
        return {"status": "error", "message": "Invalid rating value provided."}

    try:
        async with async_session_factory() as session:
            # استرجاع الرسالة مع تحميل المحادثة المرتبطة (Eager Loading) للتحقق من الملكية
            stmt = (
                select(Message)
                .options(selectinload(Message.conversation))
                .where(Message.id == message_id)
            )
            result = await session.execute(stmt)
            message_to_rate = result.scalar_one_or_none()

            if not message_to_rate:
                return {
                    "status": "error",
                    "message": f"Message with ID {message_id} not found.",
                }

            # --- [بروتوكول الأمان] ---
            # التحقق من أن المستخدم يملك المحادثة التي تحتوي الرسالة
            # ملاحظة: message_to_rate.conversation لا يمكن أن يكون None بسبب العلاقة الإلزامية،
            # ولكن قد نحتاج للتحقق الدفاعي إذا كان الـ Schema يسمح بـ NULL.
            if (
                not message_to_rate.conversation
                or message_to_rate.conversation.user_id != user_id
            ):
                logger.warning(
                    f"تنبيه أمني: حاول المستخدم {user_id} تقييم الرسالة {message_id} التي لا يملكها."
                )
                return {
                    "status": "error",
                    "message": "Permission denied. You can only rate your own conversations.",
                }

            if hasattr(message_to_rate, "rating"):
                message_to_rate.rating = rating
                await session.commit()
            else:
                logger.warning("نموذج الرسالة لا يحتوي على حقل 'rating'. تخطي التحديث.")

            logger.info(f"قام المستخدم {user_id} بتقييم الرسالة {message_id} بـ '{rating}'.")
            return {
                "status": "success",
                "message": f"Message {message_id} has been rated as '{rating}'.",
            }

    except sqlalchemy_exc.SQLAlchemyError as e:
        logger.error(f"خطأ في قاعدة البيانات أثناء تقييم الرسالة {message_id}: {e}", exc_info=True)
        return {"status": "error", "message": "A database error occurred."}
    except Exception as e:
        logger.error(f"خطأ غير متوقع أثناء تقييم الرسالة {message_id}: {e}", exc_info=True)
        return {"status": "error", "message": "An unexpected error occurred."}
