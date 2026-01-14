"""
وكيل تحليل الأداء (Analytics Agent).

مسؤول عن:
1. تشخيص مستوى الطالب بدقة.
2. توليد تقارير أداء تفصيلية.
3. تحديد نقاط القوة والضعف.
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

        yield "جاري جمع بيانات الأداء وتحليل السجلات... 📊\n"

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
        تنسيق التقرير النهائي بصيغة احترافية.
        """
        metrics = report.get("metrics", {})
        indicators = report.get("performance_indicators", {})
        recommendations = report.get("recommendations", [])

        response = [
            "## تقرير الأداء التشخيصي",
            f"**حالة الطالب:** {curve.get('trend', 'Unknown')} trend",
            "",
            "### 📈 المؤشرات الرئيسية",
            f"- **نسبة الإكمال:** {metrics.get('completion_rate', '0%')}",
            f"- **المهام النشطة:** {metrics.get('active_missions', 0)}",
            f"- **التفاعل:** {metrics.get('total_interactions', 0)} رسالة",
            "",
            "### 🧠 التحليل العميق",
            f"- **سرعة التعلم:** {curve.get('learning_velocity', 'N/A')}",
            f"- **الاستمرارية:** {curve.get('consistency', 'N/A')}",
            "",
            "### 💡 التوصيات المقترحة",
        ]

        for rec in recommendations:
            response.append(f"- {rec}")

        return "\n".join(response)
