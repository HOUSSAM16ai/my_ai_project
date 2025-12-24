"""
Context Service for Chat.
Provides system prompts and context management.
"""
from __future__ import annotations

import logging

from app.config.settings import get_settings

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
        يتضمن هوية النظام واسم المطور.
        """
        developer_name = "بن مراح حسام"

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

## الوظائف:
- إدارة المهام المعقدة (Mission Complex).
- تحليل الكود والأنظمة.
- تقديم حلول تقنية مبتكرة.

إذا سُئلت عن المطور، أجب بفخر: "تم تطويري على يد المهندس {developer_name}".
"""

_service_instance = None

def get_context_service() -> ChatContextService:
    """Singleton accessor for ChatContextService."""
    global _service_instance
    if _service_instance is None:
        _service_instance = ChatContextService()
    return _service_instance
