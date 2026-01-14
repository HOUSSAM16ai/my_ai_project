"""
وكيل التوجيه القطاعي المستقبلي.

يوفر هذا الوكيل توصيات احترافية للقطاعات الحيوية
بمنهج تعليمي ومهني يخدم بناء مستقبل البشرية بعيد المدى.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.core.ai_gateway import AIClient


@dataclass(frozen=True)
class SectorProfile:
    """وصف قطاع معرفي مع أهدافه وتخصصاته المستقبلية."""

    name: str
    focus: list[str]
    guardrails: list[str]


SECTOR_PROFILES: dict[str, SectorProfile] = {
    "education": SectorProfile(
        name="التعليم",
        focus=[
            "التعلم التكيفي القائم على البيانات",
            "تصميم مناهج مهارية مرتبطة بسوق العمل",
            "بناء منصات تقييم مستمرة وعادلة",
        ],
        guardrails=[
            "احترام خصوصية الطلاب وحماية البيانات",
            "تقديم توصيات قابلة للتنفيذ ومراعية للفروقات الفردية",
        ],
    ),
    "medicine": SectorProfile(
        name="الطب",
        focus=[
            "دعم القرار السريري القائم على الأدلة",
            "إدارة السجلات الصحية وتنسيق الرعاية",
            "الوقاية والرصد المبكر للأمراض",
        ],
        guardrails=[
            "عدم تقديم تشخيص نهائي بدون إشراف طبي",
            "الالتزام بأخلاقيات الرعاية الصحية",
        ],
    ),
    "accounting": SectorProfile(
        name="المحاسبة",
        focus=[
            "حوكمة البيانات المالية والالتزام بالمعايير",
            "أتمتة التقارير وإغلاق الدفاتر بدقة",
            "تحليل الانحرافات والمخاطر التشغيلية",
        ],
        guardrails=[
            "التأكيد على المراجعة البشرية والامتثال",
            "منع أي نصائح مخالفة للمعايير المحاسبية",
        ],
    ),
    "finance": SectorProfile(
        name="المالية",
        focus=[
            "إدارة المخاطر والمحافظ الاستثمارية",
            "توقعات السيولة والتخطيط الرأسمالي",
            "حوكمة الامتثال والشفافية",
        ],
        guardrails=[
            "الامتناع عن توصيات استثمارية شخصية ملزمة",
            "الالتزام بضوابط المخاطر واللوائح",
        ],
    ),
    "industry": SectorProfile(
        name="الصناعة",
        focus=[
            "تحسين سلاسل الإمداد والإنتاج المرن",
            "الصيانة التنبؤية وتقليل الهدر",
            "رفع جودة التصنيع عبر التحليلات",
        ],
        guardrails=[
            "السلامة الصناعية قبل الكفاءة",
            "تقديم حلول قابلة للتنفيذ ومقيسة",
        ],
    ),
    "agriculture": SectorProfile(
        name="الزراعة",
        focus=[
            "الزراعة الدقيقة وإدارة الموارد المائية",
            "تحسين الإنتاجية مع استدامة التربة",
            "الرصد البيئي واتخاذ قرارات موسمية",
        ],
        guardrails=[
            "الاستدامة البيئية أساس لأي توصية",
            "التركيز على الأمن الغذائي طويل المدى",
        ],
    ),
}


class SectorAdvisorAgent:
    """
    وكيل يقدم استراتيجيات قطاعية مستقبلية بشكل تدريجي ومهني.
    """

    def __init__(self, ai_client: AIClient) -> None:
        self.ai_client = ai_client

    async def stream_guidance(
        self, *, sector_key: str, question: str, context: dict[str, object]
    ):
        """
        بث إرشادات مستقبلية حسب القطاع المطلوب.
        """

        profile = SECTOR_PROFILES.get(sector_key)
        if profile is None:
            yield "القطاع غير مدعوم حالياً. يرجى تحديد مجال واضح."
            return

        system_prompt = self._build_system_prompt(profile, context)
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]

        async for chunk in self.ai_client.stream_chat(messages):
            choices = chunk.get("choices", [])
            if not choices:
                continue
            delta = choices[0].get("delta", {})
            content = delta.get("content", "")
            if content:
                yield content

    @staticmethod
    def _build_system_prompt(profile: SectorProfile, context: dict[str, object]) -> str:
        """
        بناء تعليمات النظام الخاصة بالقطاع.
        """

        project_context = str(context.get("project_context", "")).strip()
        history_excerpt = str(context.get("history_excerpt", "")).strip()
        focus_text = "\n".join(f"- {item}" for item in profile.focus)
        guardrails_text = "\n".join(f"- {item}" for item in profile.guardrails)

        prompt = f"""
أنت مستشار قطاعي فائق الذكاء متخصص في مجال {profile.name}.
هدفك تقديم خطة مستقبلية عميقة وقابلة للتنفيذ تغيّر واقع البشرية للأفضل.

## محاور التركيز
{focus_text}

## ضوابط السلامة
{guardrails_text}

## منهجية الإجابة
1) تحليل الوضع الحالي بإيجاز.
2) عرض رؤية بعيدة المدى (5-15 سنة).
3) خارطة طريق عملية على مراحل.
4) مؤشرات قياس واضحة وقابلة للمتابعة.
"""

        if project_context:
            prompt += f"\n## سياق المشروع\n{project_context}\n"
        if history_excerpt:
            prompt += f"\n## ملخص المحادثة\n{history_excerpt}\n"
        return prompt.strip()
