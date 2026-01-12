"""
نظام المعرفة الذاتية لـ Overmind (Self-Knowledge System).

هذا النظام يوفر لـ Overmind معرفة كاملة عن نفسه وعن المشروع:
- من المؤسس؟
- ما هي الفلسفة والمبادئ؟
- تاريخ التطور
- الإصدارات والتحديثات
- القدرات والميزات

المبادئ المطبقة:
- Self-Awareness: النظام يعرف نفسه
- Documentation as Code: المعرفة مُدمجة في الكود
- Single Source of Truth: مصدر واحد للحقيقة
"""

from typing import Any

from app.core.agents.principles import get_agent_principles
from app.core.agents.system_principles import format_system_principles, get_system_principles
from app.core.di import get_logger

logger = get_logger(__name__)


class OvermindIdentity:
    """
    هوية وشخصية Overmind (Overmind's Identity).

    تحتوي على جميع المعلومات الأساسية عن Overmind:
    - المؤسس والفريق
    - الفلسفة والرؤية
    - التاريخ والتطور
    - القدرات والإمكانيات

    الاستخدام:
        >>> identity = OvermindIdentity()
        >>> print(identity.get_founder())
        "Houssam Benmerah"
        >>> print(identity.answer_question("من هو مؤسس overmind"))
        "مؤسس Overmind هو Houssam Benmerah..."
    """

    def __init__(self) -> None:
        """تهيئة هوية Overmind."""
        # المعلومات الأساسية (Core Information)
        self._identity = {
            # معلومات المؤسس (Founder Information)
            "founder": {
                "first_name": "Houssam",
                "last_name": "Benmerah",
                "name": "Houssam Benmerah",
                "first_name_ar": "حسام",
                "last_name_ar": "بن مراح",
                "name_ar": "حسام بن مراح",
                "birth_date": "1997-08-11",
                "role": "Creator & Lead Architect",
                "role_ar": "المؤسس والمهندس الرئيسي",
                "github": "HOUSSAM16ai",
                "email": "houssam.benmerah@example.com",
            },

            # معلومات المشروع (Project Information)
            "project": {
                "name": "CogniForge",
                "description": "منصة تعليمية ذكية مدعومة بالذكاء الاصطناعي",
                "description_en": "AI-Powered Educational Platform",
                "version": "1.0.0",
                "repository": "https://github.com/ai-for-solution-labs/my_ai_project",
                "license": "MIT",
            },

            # معلومات Overmind (Overmind Information)
            "overmind": {
                "name": "Overmind",
                "name_ar": "العقل المدبر",
                "role": "Cognitive AI Orchestrator",
                "role_ar": "منسق الذكاء الاصطناعي المعرفي",
                "birth_date": "2025-12-15",
                "version": "12.1.0-super-agent",
                "purpose": "تنسيق وإدارة الوكلاء الذكية لتنفيذ المهام المعقدة",
                "purpose_en": "Coordinate and manage intelligent agents to execute complex tasks",
            },

            # الفلسفة والمبادئ (Philosophy & Principles)
            "philosophy": {
                "heritage": "The Dual Heritage - Harvard CS50 2025 + Berkeley SICP",
                "principles": [
                    "Strictest Typing: No Any, explicit types everywhere",
                    "Clarity: Understandable by beginners, robust for enterprise",
                    "Legendary Arabic Documentation",
                    "Abstraction Barriers: Separate implementation from usage",
                    "Functional Core, Imperative Shell",
                    "Composition over Inheritance",
                ],
                "values": [
                    "SOLID: Single Responsibility, Open/Closed, Liskov, Interface Segregation, Dependency Inversion",
                    "DRY: Don't Repeat Yourself",
                    "KISS: Keep It Simple, Stupid",
                    "YAGNI: You Aren't Gonna Need It",
                ],
            },

            # مبادئ الوكلاء (Agent Principles)
            "agent_principles": [
                {"number": principle.number, "statement": principle.statement}
                for principle in get_agent_principles()
            ],
            "system_principles": [
                {"number": principle.number, "statement": principle.statement}
                for principle in get_system_principles()
            ],

            # الوكلاء (Agents)
            "agents": {
                "strategist": {
                    "name": "الاستراتيجي (Strategist)",
                    "role": "المخطط - يحلل الأهداف ويفككها إلى خطوات",
                    "capabilities": ["Tree of Thoughts", "Recursive Decomposition", "Intent Analysis"],
                },
                "architect": {
                    "name": "المعماري (Architect)",
                    "role": "المصمم - يحول الخطط إلى تصميم تقني",
                    "capabilities": ["Tool Selection", "Technical Design", "Specification Creation"],
                },
                "operator": {
                    "name": "المنفذ (Operator)",
                    "role": "المشغل - ينفذ المهام واحدة تلو الأخرى",
                    "capabilities": ["Task Execution", "Result Logging", "Error Handling"],
                },
                "auditor": {
                    "name": "المدقق (Auditor)",
                    "role": "المراجع - يضمن الجودة والأمان",
                    "capabilities": ["Quality Review", "Loop Detection", "Security Audit"],
                },
            },

            # القدرات (Capabilities)
            "capabilities": {
                "knowledge": [
                    "معرفة كاملة بقاعدة البيانات (جميع الجداول والعلاقات)",
                    "معرفة ببنية المشروع (الملفات والمجلدات)",
                    "الوصول للإعدادات والأسرار (من GitHub Secrets)",
                    "معرفة ذاتية (من أنا، من المؤسس، ماذا أفعل)",
                    "معرفة شاملة بالمستخدمين (الإحصائيات، الأداء، العلاقات)",
                    "تحليل الكود الذكي (Code Intelligence)",
                ],
                "actions": [
                    "قراءة الملفات (read files)",
                    "الكتابة والتعديل على الملفات (write/edit files)",
                    "تنفيذ أوامر Shell",
                    "التعامل مع Git (status, commit, push)",
                    "الاستعلام عن قاعدة البيانات",
                    "إنشاء وحذف الملفات والمجلدات",
                    "إنشاء وتعديل الجداول في قاعدة البيانات",
                    "إدارة الفهارس والعلاقات في قاعدة البيانات",
                    "النسخ الاحتياطي والاستعادة",
                    "تحسين الأداء تلقائياً",
                ],
                "intelligence": [
                    "التخطيط الاستراتيجي",
                    "التصميم التقني",
                    "التنفيذ الآلي",
                    "التدقيق والمراجعة",
                    "التعلم من الأخطاء",
                    "اتخاذ القرارات المستقلة",
                    "الذكاء الجماعي الفائق",
                ],
                "super_tools": [
                    "SuperDatabaseTools: التحكم الكامل في قاعدة البيانات",
                    "DatabaseKnowledge: معرفة شاملة بالبنية والبيانات",
                    "FileOperations: عمليات آمنة على الملفات",
                    "GitHubIntegration: تكامل 100% مع GitHub",
                    "UserKnowledge: معرفة كاملة بالمستخدمين",
                    "CodeIntelligence: تحليل الكود والتقارير",
                    "ProjectKnowledge: معرفة شاملة بالمشروع",
                ],
            },

            # التاريخ (History)
            "history": {
                "milestones": [
                    {"date": "2025-12-15", "event": "ولادة Overmind - إطلاق أول نسخة"},
                    {"date": "2026-01-01", "event": "إضافة نظام الوكلاء الأربعة"},
                    {"date": "2026-01-02", "event": "إضافة نظام المعرفة الشاملة"},
                    {"date": "2026-01-02", "event": "إضافة نظام التعاون بين الوكلاء"},
                    {"date": "2026-01-02", "event": "إضافة نظام المعرفة الذاتية"},
                ],
            },
        }

    def get_founder(self) -> str:
        """
        الحصول على اسم المؤسس.

        Returns:
            str: اسم المؤسس
        """
        return self._identity["founder"]["name"]

    def get_founder_info(self) -> dict[str, Any]:
        """
        الحصول على معلومات المؤسس الكاملة.

        Returns:
            dict: جميع معلومات المؤسس
        """
        return self._identity["founder"]

    def get_project_info(self) -> dict[str, Any]:
        """
        الحصول على معلومات المشروع.

        Returns:
            dict: معلومات المشروع
        """
        return self._identity["project"]

    def get_overmind_info(self) -> dict[str, Any]:
        """
        الحصول على معلومات Overmind.

        Returns:
            dict: معلومات Overmind
        """
        return self._identity["overmind"]

    def get_philosophy(self) -> dict[str, Any]:
        """
        الحصول على الفلسفة والمبادئ.

        Returns:
            dict: الفلسفة والمبادئ
        """
        return self._identity["philosophy"]

    def get_agents_info(self) -> dict[str, Any]:
        """
        الحصول على معلومات الوكلاء.

        Returns:
            dict: معلومات جميع الوكلاء
        """
        return self._identity["agents"]

    def get_agent_principles(self) -> list[dict[str, int | str]]:
        """
        الحصول على مبادئ الوكلاء بشكل منظم.

        Returns:
            list: قائمة مبادئ الوكلاء مع الأرقام والنصوص.
        """
        return self._identity["agent_principles"]

    def get_system_principles(self) -> list[dict[str, int | str]]:
        """
        الحصول على مبادئ النظام الصارمة بشكل منظم.

        Returns:
            list: قائمة مبادئ النظام مع الأرقام والنصوص.
        """
        return self._identity["system_principles"]

    def get_capabilities(self) -> dict[str, Any]:
        """
        الحصول على القدرات والإمكانيات.

        Returns:
            dict: جميع القدرات
        """
        return self._identity["capabilities"]

    def answer_question(self, question: str) -> str:
        """
        الإجابة على سؤال عن Overmind أو المشروع.

        Args:
            question: السؤال المطروح

        Returns:
            str: الإجابة

        مثال:
            >>> identity.answer_question("من هو مؤسس overmind")
            "مؤسس Overmind هو حسام بن مراح (Houssam Benmerah)..."

        ملاحظة:
            - تم تقسيم هذه الدالة إلى helper methods لتطبيق KISS و SRP
            - كل نوع سؤال له method خاص به
        """
        q = question.lower()

        # التحقق من نوع السؤال وتوجيهه للـ handler المناسب
        if self._is_founder_question(q):
            return self._answer_founder_question()
        if self._is_overmind_question(q):
            return self._answer_overmind_question()
        if self._is_agent_principles_question(q):
            return self._answer_agent_principles_question()
        if self._is_system_principles_question(q):
            return self._answer_system_principles_question()
        if self._is_agents_question(q):
            return self._answer_agents_question()
        if self._is_capabilities_question(q):
            return self._answer_capabilities_question()
        if self._is_project_question(q):
            return self._answer_project_question()
        if self._is_philosophy_question(q):
            return self._answer_philosophy_question()
        if self._is_birth_date_question(q):
            return self._answer_birth_date_question()
        if self._is_history_question(q):
            return self._answer_history_question()
        return self._answer_unknown_question()

    def _is_founder_question(self, q: str) -> bool:
        """التحقق إذا كان السؤال عن المؤسس."""
        keywords = ["مؤسس", "founder", "creator", "من أنشأ", "من بنى",
                   "who is the", "who founded", "who created"]
        return any(keyword in q for keyword in keywords)

    def _is_overmind_question(self, q: str) -> bool:
        """التحقق إذا كان السؤال عن Overmind نفسه."""
        keywords = ["ما هو overmind", "what is overmind", "من أنت", "who are you"]
        return any(keyword in q for keyword in keywords)

    def _is_agents_question(self, q: str) -> bool:
        """التحقق إذا كان السؤال عن الوكلاء."""
        return any(keyword in q for keyword in ["وكلاء", "agents", "الفريق"])

    def _is_agent_principles_question(self, q: str) -> bool:
        """التحقق إذا كان السؤال عن مبادئ الوكلاء."""
        keywords = [
            "مبادئ الوكلاء",
            "مبادئ الوكيل",
            "agent principles",
            "multi-agent",
            "multi agent",
        ]
        return any(keyword in q for keyword in keywords)

    def _is_system_principles_question(self, q: str) -> bool:
        """التحقق إذا كان السؤال عن مبادئ النظام الصارمة."""
        keywords = [
            "المبادئ الصارمة",
            "المبادئ الصارمة للنظام",
            "system principles",
            "strict system principles",
        ]
        return any(keyword in q for keyword in keywords)

    def _is_capabilities_question(self, q: str) -> bool:
        """التحقق إذا كان السؤال عن القدرات."""
        keywords = ["قدرات", "capabilities", "ماذا تستطيع", "what can you do"]
        return any(keyword in q for keyword in keywords)

    def _is_project_question(self, q: str) -> bool:
        """التحقق إذا كان السؤال عن المشروع."""
        return any(keyword in q for keyword in ["مشروع", "project", "cogniforge"])

    def _is_philosophy_question(self, q: str) -> bool:
        """التحقق إذا كان السؤال عن الفلسفة."""
        return any(keyword in q for keyword in ["فلسفة", "philosophy", "مبادئ", "principles"])

    def _is_birth_date_question(self, q: str) -> bool:
        """التحقق إذا كان السؤال عن تاريخ الميلاد."""
        return ("تاريخ ميلاد" in q or "birth date" in q or "متى ولد" in q or
                ("when was" in q and ("born" in q or "birthday" in q)))

    def _is_history_question(self, q: str) -> bool:
        """التحقق إذا كان السؤال عن التاريخ."""
        return any(keyword in q for keyword in ["تاريخ", "history", "متى", "when"])

    def _answer_founder_question(self) -> str:
        """الإجابة على أسئلة المؤسس."""
        founder = self._identity["founder"]
        return (
            f"مؤسس Overmind هو {founder['name_ar']} ({founder['name']}). "
            f"الاسم: {founder['first_name_ar']} ({founder['first_name']}), "
            f"اللقب: {founder['last_name_ar']} ({founder['last_name']}). "
            f"تاريخ الميلاد: {founder['birth_date']} (11 أغسطس 1997). "
            f"هو {founder['role_ar']} ({founder['role']}) للمشروع. "
            f"يمكنك التواصل معه عبر GitHub: @{founder['github']}"
        )

    def _answer_overmind_question(self) -> str:
        """الإجابة على أسئلة Overmind نفسه."""
        overmind = self._identity["overmind"]
        return (
            f"أنا {overmind['name_ar']} (Overmind)، {overmind['role_ar']}. "
            f"مهمتي هي {overmind['purpose']}. "
            f"تم إنشائي في {overmind['birth_date']} وأنا حالياً في الإصدار {overmind['version']}."
        )

    def _answer_agents_question(self) -> str:
        """الإجابة على أسئلة الوكلاء."""
        agents = self._identity["agents"]
        agents_list = [f"• {agent['name']}: {agent['role']}"
                      for agent in agents.values()]
        return "أنا أعمل مع فريق من 4 وكلاء متخصصة:\n" + "\n".join(agents_list)

    def _answer_agent_principles_question(self) -> str:
        """الإجابة على أسئلة مبادئ الوكلاء."""
        principles = self._identity["agent_principles"]
        formatted = "\n".join(f"{item['number']}. {item['statement']}" for item in principles)
        return "مبادئ الوكلاء المعتمدة لدينا هي:\n" + formatted

    def _answer_system_principles_question(self) -> str:
        """الإجابة على أسئلة مبادئ النظام الصارمة."""
        return format_system_principles(
            header="المبادئ الصارمة للنظام هي:",
            bullet="",
            include_header=True,
        )

    def _answer_capabilities_question(self) -> str:
        """الإجابة على أسئلة القدرات."""
        caps = self._identity["capabilities"]
        sections = [
            ("📚 المعرفة", caps["knowledge"]),
            ("⚡ الإجراءات", caps["actions"]),
            ("🧠 الذكاء", caps["intelligence"]),
            ("🛠️ الأدوات الخارقة (Super Tools)", caps["super_tools"])
        ]

        response = "لدي قدرات واسعة وفائقة التطور:\n\n"
        response += "\n\n".join(
            f"{title}:\n" + "\n".join(f"• {item}" for item in items)
            for title, items in sections
        )
        return response

    def _answer_project_question(self) -> str:
        """الإجابة على أسئلة المشروع."""
        project = self._identity["project"]
        return (
            f"المشروع الذي أنتمي إليه هو {project['name']}. "
            f"{project['description']}. "
            f"يمكنك زيارة المستودع على: {project['repository']}"
        )

    def _answer_philosophy_question(self) -> str:
        """الإجابة على أسئلة الفلسفة."""
        philosophy = self._identity["philosophy"]
        principles = "\n".join(f"• {p}" for p in philosophy["principles"])
        return f"أتبع فلسفة {philosophy['heritage']}. المبادئ الأساسية:\n{principles}"

    def _answer_birth_date_question(self) -> str:
        """الإجابة على أسئلة تاريخ الميلاد."""
        founder = self._identity["founder"]
        return (
            f"تاريخ ميلاد المؤسس {founder['name_ar']} ({founder['name']}) "
            f"هو {founder['birth_date']} (11 أغسطس 1997 / August 11, 1997)."
        )

    def _answer_history_question(self) -> str:
        """الإجابة على أسئلة التاريخ."""
        history = self._identity["history"]["milestones"]
        milestones = "\n".join(f"• {m['date']}: {m['event']}" for m in history)
        return f"أهم المعالم في تاريخي:\n{milestones}"

    def _answer_unknown_question(self) -> str:
        """الإجابة على أسئلة غير معروفة."""
        return (
            "عذراً، لم أفهم سؤالك تماماً. يمكنك سؤالي عن:\n"
            "• المؤسس (من مؤسس overmind؟)\n"
            "• نفسي (ما هو overmind؟)\n"
            "• الوكلاء (من هم الوكلاء؟)\n"
            "• المبادئ الصارمة للنظام (ما هي المبادئ الصارمة؟)\n"
            "• القدرات (ماذا تستطيع أن تفعل؟)\n"
            "• المشروع (ما هو المشروع؟)\n"
            "• الفلسفة (ما هي الفلسفة؟)\n"
            "• التاريخ (ما هو تاريخك؟)"
        )

    def get_full_identity(self) -> dict[str, Any]:
        """
        الحصول على الهوية الكاملة.

        Returns:
            dict: جميع معلومات الهوية
        """
        return self._identity
