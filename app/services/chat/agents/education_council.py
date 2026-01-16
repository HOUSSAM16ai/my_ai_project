"""
مجلس الجودة التعليمية الموحّد.

يهدف هذا المكوّن إلى توحيد خبرة الوكلاء المتعددين في تعليم عالي الجودة،
مع تحويل سياق الطالب إلى "ملف تعليمي موحّد" يمكن استهلاكه عبر جميع المسارات.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.services.chat.tools import ToolRegistry


@dataclass(frozen=True, slots=True)
class EducationQualityCharter:
    """
    ميثاق الجودة التعليمية.

    يعرّف القيم الأساسية التي يجب أن يلتزم بها أي وكيل عند بناء إجابة تعليمية.
    """

    title: str
    pillars: tuple[str, ...]
    promises: tuple[str, ...]

    def render(self) -> str:
        """صياغة الميثاق بنص موحّد للاستخدام داخل المطالبات."""
        lines = [f"{self.title}:"]
        lines.extend([f"- {pillar}" for pillar in self.pillars])
        lines.append("وعود الجودة:")
        lines.extend([f"- {promise}" for promise in self.promises])
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class EducationResponseRubric:
    """
    معيار جودة الاستجابة التعليمية.

    يضمن أن الرد يمر بمراحل تفسيرية واضحة ويخضع لفحوص جودة نهائية.
    """

    phases: tuple[str, ...]
    quality_checks: tuple[str, ...]

    def render(self) -> str:
        """صياغة المعيار كنص إرشادي للردود التعليمية."""
        lines = ["معيار الردود التعليمية:"]
        lines.append("مراحل الإجابة:")
        lines.extend([f"- {phase}" for phase in self.phases])
        lines.append("فحوص الجودة:")
        lines.extend([f"- {check}" for check in self.quality_checks])
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class EducationBrief:
    """
    موجز تعليمي موحّد للاستخدام عبر الوكلاء.

    يجمع الميثاق، ملف الطالب، إشارات التعلم، وضوابط الجودة في قالب واحد.
    """

    charter: EducationQualityCharter
    student_summary: tuple[str, ...]
    learning_curve: tuple[str, ...]
    guardrails: tuple[str, ...]
    rubric: EducationResponseRubric
    focus_directives: tuple[str, ...]

    def render(self) -> str:
        """تحويل الموجز إلى نص موحد قابل للإدراج في تعليمات النظام."""
        sections: list[str] = [self.charter.render(), self.rubric.render()]

        if self.focus_directives:
            sections.append("\nبوصلة التخصيص والتوجيه:")
            sections.extend([f"- {line}" for line in self.focus_directives])

        if self.student_summary:
            sections.append("\nملف الطالب المختصر:")
            sections.extend([f"- {line}" for line in self.student_summary])

        if self.learning_curve:
            sections.append("\nمنحنى التعلم:")
            sections.extend([f"- {line}" for line in self.learning_curve])

        if self.guardrails:
            sections.append("\nضوابط الجودة والانضباط:")
            sections.extend([f"- {line}" for line in self.guardrails])

        return "\n".join(sections)


class EducationCouncil:
    """
    مجلس التعليم الاحترافي.

    ينسّق بين الأدوات المختلفة لتجميع صورة تعليمية موحّدة
    تساعد كل وكيل على تقديم تعليم راقٍ ومخصص لكل طالب.
    """

    def __init__(self, tools: ToolRegistry) -> None:
        """تهيئة المجلس مع سجل الأدوات المعتمد في المنظومة."""
        self.tools = tools

    async def build_brief(self, *, context: dict[str, object]) -> EducationBrief:
        """
        بناء موجز تعليمي موحّد اعتمادًا على سياق الطالب.

        Args:
            context: سياق الطلب الحالي (يتضمن user_id عند توفره).

        Returns:
            EducationBrief: موجز تعليمي شامل.
        """
        charter = self._build_quality_charter()
        rubric = self._build_response_rubric()
        guardrails = self._build_guardrails()
        focus_directives = self._build_focus_directives(context)
        student_summary: tuple[str, ...] = ()
        learning_curve: tuple[str, ...] = ()

        user_id = context.get("user_id")
        if isinstance(user_id, int):
            student_summary = await self._build_student_summary(user_id)
            learning_curve = await self._build_learning_curve(user_id)

        return EducationBrief(
            charter=charter,
            student_summary=student_summary,
            learning_curve=learning_curve,
            guardrails=guardrails,
            rubric=rubric,
            focus_directives=focus_directives,
        )

    def _build_quality_charter(self) -> EducationQualityCharter:
        """
        بناء ميثاق الجودة الموحد للردود التعليمية.
        """
        return EducationQualityCharter(
            title="ميثاق التعليم الراقي (Elite Learning Charter)",
            pillars=(
                "الوضوح العميق مع بساطة العرض التدريجي.",
                "التخصيص وفق ملف الطالب مع احترام الفروق الفردية.",
                "التركيز على المنهجية والتفكير المنطقي قبل الإجابة النهائية.",
                "الترابط بين المفاهيم والمهارات التطبيقية.",
                "التغذية الراجعة التشخيصية التي تقود للتحسن المستمر.",
            ),
            promises=(
                "عدم الاكتفاء بالنتيجة دون شرح آلية التفكير.",
                "تقديم أمثلة عند الحاجة لتثبيت المفاهيم.",
                "اختبار فهم الطالب بأسئلة قصيرة داعمة.",
            ),
        )

    def _build_guardrails(self) -> tuple[str, ...]:
        """
        بناء ضوابط الالتزام التعليمية.
        """
        return (
            "عدم اختلاق تمارين أو امتحانات رسمية غير موثقة.",
            "اعتماد السياق المتاح وعدم تجاوز حدود المعرفة المقدمة.",
            "الحفاظ على نبرة محترفة داعمة ومحفزة.",
            "التصريح عند نقص البيانات والاقتراح بخطوات بديلة.",
        )

    def _build_response_rubric(self) -> EducationResponseRubric:
        """
        بناء معيار الجودة للاستجابة التعليمية الراقية.
        """
        return EducationResponseRubric(
            phases=(
                "تلخيص الهدف التعليمي بلغة الطالب.",
                "شرح المفهوم الأساسي بصورة متدرجة.",
                "تحويل الشرح إلى خطوات منهجية قابلة للتطبيق.",
                "تثبيت الفهم بسؤال قصير أو تمرين موجّه.",
                "خاتمة محفزة تشير للخطوة التالية.",
            ),
            quality_checks=(
                "الوضوح بدون حشو أو تعقيد زائد.",
                "عدم تقديم الحل النهائي إن كان تمرينًا تقييميًا.",
                "تطابق النبرة مع مستوى الطالب واحتياجاته.",
                "ربط المفهوم بالتطبيق الواقعي أو الأكاديمي.",
            ),
        )

    def _build_focus_directives(self, context: dict[str, object]) -> tuple[str, ...]:
        """
        بناء توجيهات تخصيصية تعتمد على السياق الحالي.
        """
        focus: list[str] = []
        intent = context.get("intent")
        if intent is not None:
            focus.append(f"نية التفاعل الحالية: {intent}")
        intent_type = context.get("intent_type")
        if isinstance(intent_type, str) and intent_type:
            focus.append(f"مسار التخصيص: {intent_type}")
        difficulty = context.get("difficulty")
        if isinstance(difficulty, str) and difficulty:
            focus.append(f"تفضيل الصعوبة: {difficulty}")
        language = context.get("language")
        if isinstance(language, str) and language:
            focus.append(f"لغة الشرح المفضلة: {language}")
        experience_tier = context.get("experience_tier")
        if isinstance(experience_tier, str) and experience_tier:
            focus.append(f"مستوى التجربة المطلوبة: {experience_tier}")
        if not focus:
            focus.append("اعتمد على سياق السؤال لبناء أفضل توجيه ممكن.")
        focus.append("احرص على تقديم تجربة تعليمية راقية ومنظمة بأعلى مستوى من الدقة.")
        return tuple(focus)

    async def _build_student_summary(self, user_id: int) -> tuple[str, ...]:
        """
        بناء ملخص للطالب اعتمادًا على سجله التعليمي.
        """
        try:
            payload = await self.tools.execute(
                "fetch_comprehensive_student_history",
                {"user_id": user_id},
            )
        except Exception:
            return ()

        if not isinstance(payload, dict):
            return ()

        stats = payload.get("profile_stats")
        missions = payload.get("missions_summary")
        profile = self._derive_learning_profile(stats, missions)
        summary_lines = self._format_profile_summary(stats, missions, profile)
        return tuple(summary_lines)

    async def _build_learning_curve(self, user_id: int) -> tuple[str, ...]:
        """
        بناء مؤشرات منحنى التعلم للطالب.
        """
        try:
            payload = await self.tools.execute(
                "analyze_learning_curve",
                {"user_id": user_id},
            )
        except Exception:
            return ()

        if not isinstance(payload, dict):
            return ()

        status = payload.get("status")
        if isinstance(status, str) and status == "no_data":
            return ("لا توجد بيانات كافية لرسم منحنى التعلم حالياً.",)

        lines: list[str] = []
        total_completed = payload.get("total_completed")
        if isinstance(total_completed, int):
            lines.append(f"عدد المهام المكتملة: {total_completed}")
        last_active_date = payload.get("last_active_date")
        if isinstance(last_active_date, str) and last_active_date:
            lines.append(f"آخر نشاط مسجل: {last_active_date}")
        trend = payload.get("trend")
        if isinstance(trend, str) and trend:
            lines.append(f"اتجاه التعلم: {trend}")
        consistency = payload.get("consistency_score")
        if isinstance(consistency, str) and consistency:
            lines.append(f"مؤشر الثبات: {consistency}")

        return tuple(lines)

    def _derive_learning_profile(
        self,
        stats: object,
        missions: object,
    ) -> dict[str, str]:
        """
        اشتقاق مستوى الطالب ونبرة الإرشاد المطلوبة من البيانات المتاحة.
        """
        level = "متوسط"
        tone = "مشجع"
        pacing = "متوازن"

        if isinstance(stats, dict):
            total_missions = stats.get("total_missions")
            completed_missions = stats.get("completed_missions")
            failed_missions = stats.get("failed_missions")
            total_messages = stats.get("total_chat_messages")

            if isinstance(total_missions, int) and total_missions <= 1:
                level = "مبتدئ"
                pacing = "بطيء مع خطوات واضحة"
            if isinstance(completed_missions, int) and isinstance(total_missions, int) and total_missions > 0:
                completion_ratio = completed_missions / total_missions
                if completion_ratio >= 0.75:
                    level = "متقدم"
                    pacing = "سريع مع تحديات إضافية"
            if isinstance(failed_missions, int) and failed_missions >= 2:
                tone = "داعِم مع إعادة تبسيط"
                pacing = "متدرج مع أمثلة إضافية"
            if isinstance(total_messages, int) and total_messages < 5:
                tone = "ترحيبي وهادئ"

        focus = "الربط بين الفكرة والخطوات العملية"
        if isinstance(missions, dict):
            topics = missions.get("topics")
            if isinstance(topics, list):
                topic_list = [topic for topic in topics if isinstance(topic, str)]
                if topic_list:
                    focus = f"ربط الشرح بمواضيع الطالب الحديثة مثل: {', '.join(topic_list[:3])}"

        return {
            "level": level,
            "tone": tone,
            "pacing": pacing,
            "focus": focus,
        }

    def _format_profile_summary(
        self,
        stats: object,
        missions: object,
        profile: dict[str, str],
    ) -> list[str]:
        """
        صياغة ملخص شخصي قابل للإدراج داخل تعليمات الوكيل.
        """
        lines: list[str] = [
            f"مستوى تقريبي: {profile['level']}",
            f"أسلوب الشرح: {profile['tone']}، بإيقاع {profile['pacing']}",
            f"محور التركيز: {profile['focus']}",
        ]

        if isinstance(stats, dict):
            total_missions = stats.get("total_missions")
            completed_missions = stats.get("completed_missions")
            failed_missions = stats.get("failed_missions")
            total_messages = stats.get("total_chat_messages")
            last_activity = stats.get("last_activity")
            if isinstance(total_missions, int):
                lines.append(f"إجمالي المهام: {total_missions}")
            if isinstance(completed_missions, int):
                lines.append(f"المهام المكتملة: {completed_missions}")
            if isinstance(failed_missions, int):
                lines.append(f"المهام غير المكتملة: {failed_missions}")
            if isinstance(total_messages, int):
                lines.append(f"إجمالي رسائل التعلم: {total_messages}")
            if isinstance(last_activity, str) and last_activity:
                lines.append(f"آخر نشاط: {last_activity}")

        if isinstance(missions, dict):
            topics = missions.get("topics")
            recent = missions.get("recent_missions")
            if isinstance(topics, list):
                topic_list = [topic for topic in topics if isinstance(topic, str)]
                if topic_list:
                    lines.append(f"مواضيع حديثة: {', '.join(topic_list[:6])}")
            if isinstance(recent, list) and recent:
                latest = recent[0]
                if isinstance(latest, dict):
                    title = latest.get("title")
                    status = latest.get("status")
                    if isinstance(title, str) and isinstance(status, str):
                        lines.append(f"آخر مهمة: {title} ({status})")

        return lines
