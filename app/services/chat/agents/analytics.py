"""
وكيل تحليل الأداء (Analytics Agent) - النسخة المحسنة.

يستخدم بيانات حقيقية لتقديم تقارير دقيقة ومخصصة.
"""

from typing import AsyncGenerator

from app.core.logging import get_logger
from app.services.chat.tools import ToolRegistry

logger = get_logger("analytics-agent")


class AnalyticsAgent:
    """
    وكيل متخصص في تحليل بيانات الطلاب التعليمية وتقديم تقارير تشخيصية.
    """

    def __init__(self, tools: ToolRegistry) -> None:
        self.tools = tools

    async def process(self, context: dict[str, object]) -> AsyncGenerator[str, None]:
        """
        تنفيذ عملية التحليل بناءً على السياق.
        """
        logger.info("Analytics agent started processing")

        user_id = context.get("user_id")
        if not user_id:
            yield "عذراً، لم أتمكن من تحديد هوية المستخدم لتحليل بياناته."
            return

        yield "🔍 **جاري تحليل سجلك التعليمي بالكامل...**\n"

        # 1. Fetch Diagnostic Report
        try:
            report = await self.tools.execute("get_student_diagnostic_report", {"user_id": user_id})
        except Exception as e:
            logger.error(f"Error fetching report: {e}")
            yield "حدث خطأ أثناء جلب تقرير الأداء."
            return

        if "error" in report:
            yield f"تعذر الوصول لبيانات الطالب: {report.get('error')}"
            return

        # 2. Analyze Learning Curve
        try:
            curve = await self.tools.execute("analyze_learning_curve", {"user_id": user_id})
        except Exception as e:
            logger.warning(f"Error analyzing curve: {e}")
            curve = {}

        # 3. Stream the formatted response
        yield self._format_response(report, curve)

    def _format_response(self, report: dict, curve: dict) -> str:
        """
        تنسيق التقرير النهائي بصيغة احترافية تتفاعل مع المحتوى الحقيقي.
        """
        metrics = report.get("metrics", {})
        recent = report.get("recent_activity", [])
        topics = report.get("topics_covered", [])
        recommendations = report.get("recommendations", [])

        # بناء قائمة المهام الحديثة
        recent_list = ""
        if recent:
            for m in recent:
                icon = "✅" if m['status'] == 'success' else "⏳"
                recent_list += f"- {icon} **{m['title']}** ({m['date'][:10]})\n"
        else:
            recent_list = "لا توجد نشاطات حديثة.\n"

        # بناء المواضيع
        topics_str = ", ".join(topics) if topics else "عام"

        response = [
            "## 📊 تقرير الأداء الشخصي",
            f"مرحباً بك. قمت بتحليل {metrics.get('total_missions')} مهمة تعليمية خاصة بك.",
            "",
            "### 📈 مؤشرات الإنجاز",
            f"- **نسبة النجاح:** {metrics.get('completion_rate', '0%')}",
            f"- **المهام المكتملة:** {metrics.get('completed_missions', 0)}",
            f"- **المواضيع التي ركزت عليها:** {topics_str}",
            "",
            "### 🕒 النشاط الأخير",
            recent_list,
            "",
            "### 💡 تشخيص الذكاء الاصطناعي",
            f"- **نمط التعلم:** {curve.get('trend', 'غير محدد')}",
            f"- **الاستمرارية:** {curve.get('consistency_score', 'N/A')}",
            "",
            "### 🚀 الخطوات القادمة المقترحة",
        ]

        for rec in recommendations:
            response.append(f"- {rec}")

        return "\n".join(response)
