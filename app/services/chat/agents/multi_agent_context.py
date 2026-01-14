"""
باني سياق الوكلاء المتعددين للمحادثة الخارقة.

يوفر هذا الملف طبقة وظيفية لبناء السياق المطلوب للوكلاء
من دون مزج تفاصيل التنفيذ مع منطق المنسق.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.chat.context_service import get_context_service
from app.services.chat.agents.api_first_framework import get_framework_overview
from app.services.project_context.application.context_analyzer import ProjectContextService
from app.services.project_context.domain.models import CodeStatistics, ProjectStructure


@dataclass(frozen=True)
class MultiAgentContext:
    """حاوية سياق موحّدة للوكلاء المتعددين."""

    system_prompt: str
    project_context: str
    history_excerpt: str
    api_first_framework: str

    def to_payload(self) -> dict[str, object]:
        """تحويل السياق إلى حمولة معجمية قابلة للإرسال."""

        return {
            "system_prompt": self.system_prompt,
            "project_context": self.project_context,
            "history_excerpt": self.history_excerpt,
            "api_first_framework": self.api_first_framework,
        }


class MultiAgentContextBuilder:
    """
    باني سياق متعدد الوكلاء وفق مبدأ الفصل بين المنطق والتنفيذ.
    """

    def __init__(self, project_context: ProjectContextService | None = None) -> None:
        self._project_context = project_context or ProjectContextService()

    def build(
        self, *, question: str, history: list[dict[str, str]], role: str = "customer"
    ) -> MultiAgentContext:
        """
        بناء سياق شامل للوكلاء المتعددين.

        Args:
            question: سؤال المستخدم الحالي.
            history: سجل المحادثة المختصر.
            role: نوع المسار (admin/customer).

        Returns:
            MultiAgentContext: السياق النهائي للوكلاء.
        """

        context_service = get_context_service()
        if role == "admin":
            system_prompt = context_service.get_admin_system_prompt()
            project_context = self._project_context.generate_context_for_ai()
        else:
            system_prompt = context_service.get_customer_system_prompt()
            project_context = self._build_project_brief()

        api_first_framework = self._build_api_first_framework()
        history_excerpt = self._summarize_history(history, question)
        return MultiAgentContext(
            system_prompt=system_prompt,
            project_context=project_context,
            history_excerpt=history_excerpt,
            api_first_framework=api_first_framework,
        )

    def _build_project_brief(self) -> str:
        """تلخيص خفيف لسياق المشروع لواجهة الزبون."""

        stats = self._project_context.get_code_statistics()
        structure = self._project_context.get_project_structure()
        return "\n".join(self._render_brief(stats, structure))

    @staticmethod
    def _render_brief(stats: CodeStatistics, structure: ProjectStructure) -> list[str]:
        """صياغة مختصر للمشروع بصيغة تعليمية موجزة."""

        top_dirs = ", ".join(dir_info.name for dir_info in structure.directories[:5])
        return [
            "## ملخص المشروع",
            f"- ملفات Python: {stats.python_files}",
            f"- ملفات الاختبار: {stats.test_files}",
            f"- إجمالي الأسطر: {stats.total_lines}",
            f"- أبرز المجلدات: {top_dirs if top_dirs else 'غير متاح'}",
        ]

    @staticmethod
    def _summarize_history(history: list[dict[str, str]], question: str) -> str:
        """اختصار سجل المحادثة في سطور موجزة قابلة للتضمين."""

        trimmed = history[-4:] if len(history) > 4 else history
        formatted = [f"{item.get('role', 'user')}: {item.get('content', '')}" for item in trimmed]
        formatted.append(f"user: {question}")
        return "\n".join(formatted)

    @staticmethod
    def _build_api_first_framework() -> str:
        """صياغة موجزة لإطار API First لتضمينه في سياق الوكلاء."""

        overview = get_framework_overview()
        lines = ["## إطار API First (مختصر)"]
        for unit in overview:
            lines.append(f"- {unit['unit_id']}. {unit['title']}")
        return "\n".join(lines)
