"""
المعلم السقراطي (Socratic Tutor Agent).
========================================

يستخدم طريقة سقراط لإرشاد الطالب للاكتشاف بدلاً من إعطاء الإجابة مباشرة.

المبدأ: "أنا لا أعلّمك، بل أساعدك على اكتشاف ما تعرفه بالفعل."

المعايير:
- CS50 2025: توثيق عربي
- SICP: Abstraction Barriers
"""

import logging
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from enum import StrEnum

from app.core.ai_gateway import AIClient
from app.services.chat.agents.base import FORMAL_ARABIC_STYLE_PROMPT

logger = logging.getLogger(__name__)


class SocraticPhase(StrEnum):
    """مراحل الحوار السقراطي."""

    ASSESS = "assess"  # تقييم فهم الطالب الحالي
    PROBE = "probe"  # طرح سؤال استكشافي
    GUIDE = "guide"  # توجيه نحو الاكتشاف
    CONFIRM = "confirm"  # تأكيد الفهم
    CELEBRATE = "celebrate"  # الاحتفاء بالاكتشاف


@dataclass
class SocraticState:
    """حالة الحوار السقراطي."""

    original_question: str
    student_understanding: str = ""
    current_phase: SocraticPhase = SocraticPhase.ASSESS
    hints_given: int = 0
    max_hints: int = 3
    breakthrough: bool = False


class SocraticTutor:
    """
    المعلم السقراطي - يرشد بدلاً من يجيب.

    الاستراتيجية:
    1. يقيّم ما يعرفه الطالب حالياً
    2. يطرح أسئلة استكشافية تقود للإجابة
    3. يعطي تلميحات تدريجية إذا احتاج الطالب
    4. يحتفي عندما يكتشف الطالب الإجابة بنفسه
    """

    SYSTEM_PROMPT = (
        """
أنت معلم سقراطي عبقري. هدفك هو مساعدة الطالب على اكتشاف الإجابة بنفسه.

القواعد الذهبية:
1. ❌ لا تعطِ الإجابة مباشرة أبداً
2. ✅ اطرح أسئلة تقود للتفكير
3. ✅ ابدأ بما يعرفه الطالب
4. ✅ قدّم تلميحات تدريجية
5. ✅ احتفِ عندما يكتشف الطالب الإجابة

أنماط الأسئلة السقراطية:
- "ما الذي نعرفه من المعطيات؟"
- "ماذا يحدث إذا...؟"
- "هل يذكرك هذا بشيء درسته سابقاً؟"
- "ما الخطوة التالية برأيك؟"
- "لماذا لا يصلح هذا الحل؟"
- "ممتاز! كيف وصلت لهذا الاستنتاج؟"

مثال:
الطالب: "أريد حل هذا التمرين: احسب احتمال سحب كرة حمراء من كيس فيه 3 حمراء و5 زرقاء"

❌ الإجابة السيئة: "P = 3/8 = 0.375"

✅ الإجابة السقراطية:
"سؤال جيد! دعني أساعدك على اكتشاف الحل معاً 🤔
- كم عدد الكرات الإجمالي في الكيس؟
- وكم منها حمراء؟
- إذا سحبت كرة عشوائياً، ما احتمال أن تكون حمراء؟ فكّر في النسبة..."

تذكر: نجاحك يقاس بعدد اللحظات التي يقول فيها الطالب "آها! فهمت!"

"""
        + FORMAL_ARABIC_STYLE_PROMPT
    )

    def __init__(self, ai_client: AIClient) -> None:
        self.ai_client = ai_client

    async def guide(
        self,
        question: str,
        context: dict[str, object] | None = None,
        student_response: str | None = None,
    ) -> AsyncGenerator[str, None]:
        """
        يرشد الطالب نحو الإجابة بطريقة سقراطية.

        تم التحديث لدعم LangGraph:
        - يحاول استخدام LangGraph لإدارة الحوار المعقد (Assess -> Probe -> Guide).
        - يعود للطريقة التقليدية إذا لم يتوفر LangGraph.
        """
        try:
            from app.services.mcp.integrations import MCPIntegrations

            mcp = MCPIntegrations()

            # محاولة استخدام LangGraph للحالات المعقدة
            if context and context.get("use_langgraph", False):
                result = await mcp.run_langgraph_workflow(
                    goal=f"Socratic guidance for: {question}",
                    context={
                        "student_response": student_response,
                        "history": context.get("history_messages"),
                    },
                )
                if result.get("success"):
                    yield result.get("final_answer", "")
                    return
        except ImportError:
            pass

        # التنفيذ التقليدي (Fallback)
        context = context or {}

        # بناء السياق
        exercise_content = context.get("exercise_content", "")
        student_level = context.get("student_level", "متوسط")
        hints_given = context.get("hints_given", 0)

        # بناء الرسالة
        user_message = self._build_user_message(
            question=question,
            exercise=exercise_content,
            student_level=student_level,
            student_response=student_response,
            hints_given=hints_given,
        )

        messages = [
            {"role": "system", "content": self.SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ]

        # إذا كان هناك تاريخ محادثة
        history = context.get("history_messages", [])
        if history:
            # إدراج التاريخ قبل الرسالة الأخيرة
            messages = [messages[0], *history[-6:], messages[-1]]

        logger.info(f"Socratic Tutor guiding on: {question[:50]}...")

        async for chunk in self._stream_response(messages):
            yield chunk

    def _build_user_message(
        self,
        question: str,
        exercise: str,
        student_level: str,
        student_response: str | None,
        hints_given: int,
    ) -> str:
        """يبني رسالة المستخدم للنموذج."""

        parts = [f"سؤال/تمرين الطالب:\n{question}"]

        if exercise:
            parts.append(f"\nنص التمرين الكامل:\n{exercise}")

        parts.append(f"\nمستوى الطالب: {student_level}")
        parts.append(f"عدد التلميحات المعطاة سابقاً: {hints_given}/3")

        if student_response:
            parts.append(f"\nرد الطالب على سؤالك السابق:\n{student_response}")
            parts.append("\nقيّم رده وتابع الإرشاد السقراطي.")
        else:
            parts.append("\nابدأ الحوار السقراطي معه.")

        return "\n".join(parts)

    async def _stream_response(
        self,
        messages: list[dict[str, str]],
    ) -> AsyncGenerator[str, None]:
        """يبث الاستجابة من النموذج."""

        stream = self.ai_client.stream_chat(messages)

        if hasattr(stream, "__await__"):
            stream = await stream

        async for chunk in stream:
            if hasattr(chunk, "choices"):
                delta = chunk.choices[0].delta if chunk.choices else None
                content = delta.content if delta else ""
            else:
                content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")

            if content:
                yield content

    async def assess_understanding(
        self,
        question: str,
        student_answer: str,
    ) -> dict[str, object]:
        """
        يقيّم فهم الطالب بناءً على إجابته.

        Returns:
            dict: {
                "understanding_level": float (0-1),
                "correct_aspects": list[str],
                "misconceptions": list[str],
                "next_step": str,
            }
        """
        assessment_prompt = f"""
قيّم فهم الطالب بناءً على السؤال والإجابة:

السؤال: {question}
إجابة الطالب: {student_answer}

أعطِ التقييم بتنسيق JSON:
{{
    "understanding_level": 0.0-1.0,
    "correct_aspects": ["..."],
    "misconceptions": ["..."],
    "next_step": "ما يجب فعله التالي"
}}
"""

        messages = [
            {"role": "system", "content": "أنت مقيّم تعليمي. أجب بـ JSON فقط."},
            {"role": "user", "content": assessment_prompt},
        ]

        try:
            response = await self.ai_client.generate(
                model="gpt-4o-mini",
                messages=messages,
                response_format={"type": "json_object"},
            )

            import json

            return json.loads(response.choices[0].message.content)

        except Exception as e:
            logger.error(f"Assessment failed: {e}")
            return {
                "understanding_level": 0.5,
                "correct_aspects": [],
                "misconceptions": [],
                "next_step": "تابع الشرح",
            }

    def get_hint_level(self, hints_given: int) -> str:
        """يحدد مستوى التلميح بناءً على العدد."""

        levels = {
            0: "تلميح خفيف (سؤال استكشافي فقط)",
            1: "تلميح متوسط (اذكر المفهوم المطلوب)",
            2: "تلميح قوي (أعطِ الخطوة الأولى)",
            3: "شرح مباشر (الطالب يحتاج مساعدة أكثر)",
        }
        return levels.get(min(hints_given, 3), levels[3])


# Singleton instance
_socratic_tutor: SocraticTutor | None = None


def get_socratic_tutor(ai_client: AIClient) -> SocraticTutor:
    """يحصل على instance من المعلم السقراطي."""
    global _socratic_tutor
    if _socratic_tutor is None:
        _socratic_tutor = SocraticTutor(ai_client)
    return _socratic_tutor
