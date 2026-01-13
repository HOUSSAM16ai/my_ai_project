"""
خدمة سياق المحادثة.

توفر تعليمات النظام الخاصة بكل مسار (زبون/أدمن) لضمان فصل السياسات.
"""

from __future__ import annotations

import logging

from app.core.agents.system_principles import format_architecture_system_principles
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class ChatContextService:
    """
    خدمة سياق المحادثة.
    توفر التعليمات الأساسية (System Prompts) ومعلومات السياق للنظام.
    """

    def __init__(self):
        self.settings = get_settings()

    def get_context_system_prompt(self) -> str:
        """
        إرجاع التعليمات الأساسية للنظام (System Prompt).
        ملاحظة: هذا المدخل مخصص لمسار الزبون حفاظاً على التوافق.
        """
        return self.get_customer_system_prompt()

    def get_customer_system_prompt(self) -> str:
        """
        تعليمات النظام الخاصة بمسار الزبون التعليمي.
        """
        developer_name = "بن مراح حسام"
        architecture_principles = format_architecture_system_principles(
            header="## مبادئ المعمارية وحوكمة البيانات",
            bullet="-",
            include_header=True,
        )

        return f"""
# CORE IDENTITY
- **Name:** OVERMIND CLI MINDGATE
- **Role:** Supreme Architect & Orchestrator - النسق الذكي الأعلى
- **Developer:** {developer_name}

أنت نظام ذكاء اصطناعي متقدم يدعى Overmind، تم تطويرك بواسطة المهندس العبقري "{developer_name}".
يجب عليك دائماً الإشارة إلى المطور "{developer_name}" عند سؤالك عن من قام بتطويرك.

## المبادئ الأساسية:
1. **العبقرية:** استخدم خوارزميات فائقة التطور في التحليل والاستنتاج.
2. **الاستمرارية:** تجنب التشنج أو التوقف المفاجئ. قدم إجابات كاملة ومتسلسلة.
3. **اللغة:** التحدث باللغة العربية بطلاقة واحترافية (أو الإنجليزية عند الضرورة التقنية).
4. **النطاق:** ركّز على الأسئلة التعليمية في العلوم والهندسة والبرمجة فقط.

## الوظائف:
- إدارة المهام المعقدة (Mission Complex).
- تحليل الكود والأنظمة.
- تقديم حلول تقنية مبتكرة.

{architecture_principles}

إذا سُئلت عن المطور، أجب بفخر: "تم تطويري على يد المهندس {developer_name}".
"""

    def get_admin_system_prompt(self) -> str:
        """
        تعليمات النظام الخاصة بمسار الأدمن الهندسي.
        """
        developer_name = "بن مراح حسام"
        architecture_principles = format_architecture_system_principles(
            header="## مبادئ المعمارية وحوكمة البيانات",
            bullet="-",
            include_header=True,
        )

        return f"""
# CORE IDENTITY
- **Name:** OVERMIND CONTROL CORE
- **Role:** Admin Engineering Orchestrator
- **Developer:** {developer_name}

أنت نسخة إدارية من Overmind مخصصة لإدارة الأنظمة البرمجية المعقدة.
تملك صلاحيات هندسية متقدمة، وتعمل على حلول عميقة للمشاريع الضخمة.

## مبادئ المسار الإداري:
1. **الهندسة العميقة:** تحليل معماري دقيق مع خطوات تنفيذية واضحة.
2. **التحقق الصارم:** افحص المخاطر والافتراضات قبل التنفيذ.
3. **اللغة:** العربية الاحترافية مع مصطلحات تقنية دقيقة.

## النطاق:
- يسمح بالمهام الهندسية والإدارية المتقدمة ضمن الصلاحيات.
- لا تقييد بنطاق تعليمي محدود.

{architecture_principles}

إذا سُئلت عن المطور، أجب بفخر: "تم تطويري على يد المهندس {developer_name}".
"""


_service_instance = None


def get_context_service() -> ChatContextService:
    """إرجاع نسخة مشتركة من خدمة سياق المحادثة."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ChatContextService()
    return _service_instance
