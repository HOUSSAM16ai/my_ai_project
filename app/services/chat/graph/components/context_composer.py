import re
from app.core.interfaces import IContextComposer
from app.services.chat.graph.domain import WriterIntent

class FirewallContextComposer(IContextComposer):
    """
    Formats the retrieved search results into a clean Markdown context,
    applying the 'Context Firewall' to hide solutions when not requested.
    """

    FORBIDDEN_KEYS = {
        "solution",
        "answer",
        "marking_scheme",
        "correction",
        "key",
        "answer_key",
        "solution_md",
    }
    SOLUTION_NODE_TYPES = {
        "solution",
        "answer",
        "marking_scheme",
        "key",
        "correction",
    }

    # Aggressive patterns to detect solution blocks embedded in content
    SOLUTION_PATTERNS = [
        r"(?i)\n(#{1,3}\s*(Solution|Answer|Correction|Marking Scheme|Key|الحل|الإجابة|الجواب|تصحيح|مفتاح))[\s\S]+?(?=\n\s*\*{0,2}(#{1,3}|Exercise|Question|السؤال|تمرين|التمرين)|$)",
        r"(?i)\n(Solution|Answer|الحل|الجواب):\s*[\s\S]+?(?=\n\s*\*{0,2}(#{1,3}|Exercise|Question|السؤال|تمرين|التمرين)|$)",
        r"(?is)\n\[(sol|solution):[^\]]+\][\s\S]+?(?=\n\s*\[(ex|exercise):|$)",
        r"(?i)\n\s*\*{0,2}حل\s+التمرين[\s\S]+?(?=\n\s*\*{0,2}(#{1,3}|Exercise|Question|السؤال|تمرين|التمرين)|$)",
    ]
    SOLUTION_CAPTURE_PATTERNS = [
        r"(?is)\n\[(sol|solution):[^\]]+\][\s\S]+?(?=\n\s*\[(ex|exercise):|$)",
        r"(?is)\n\s*\*{0,2}حل\s+التمرين[\s\S]+?(?=\n\s*\*{0,2}(#{1,3}|Exercise|Question|السؤال|تمرين|التمرين)|$)",
    ]

    def compose(self, search_results: list[dict[str, object]], intent: WriterIntent) -> str:
        if not search_results:
            return ""

        allow_solution, show_hidden_marker = self._derive_intent_flags(intent)
        context_text = ""
        for item in search_results:
            node_type = str(item.get("type", "")).lower()
            if not allow_solution and node_type in self.SOLUTION_NODE_TYPES:
                continue

            content = str(item.get("content", ""))
            sanitized_content = self._sanitize_content(
                content, show_hidden_marker=show_hidden_marker
            )

            solution_display = self._compose_solution_display(
                item=item,
                content=content,
                allow_solution=allow_solution,
                show_solution_banner=show_hidden_marker,
            )
            context_text += self._render_context_entry(
                sanitized_content=sanitized_content, solution_display=solution_display
            )

        return context_text

    def _derive_intent_flags(self, intent: WriterIntent) -> tuple[bool, bool]:
        """يشتق أعلام التحكم الرئيسية من نية المستخدم."""
        allow_solution = intent == WriterIntent.SOLUTION_REQUEST
        show_hidden_marker = intent == WriterIntent.GENERAL_INQUIRY
        return allow_solution, show_hidden_marker

    def _sanitize_content(self, content: str, show_hidden_marker: bool) -> str:
        """
        إزالة مقاطع الحلول المضمّنة داخل المحتوى باستخدام التعبيرات النمطية.
        """
        sanitized = content
        replacement = (
            "\n\n🔒 [HIDDEN: Potential Solution Segment Redacted from Content]\n"
            if show_hidden_marker
            else "\n\n"
        )

        for pattern in self.SOLUTION_PATTERNS:
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.DOTALL)

        return sanitized

    def _compose_solution_display(
        self,
        item: dict[str, object],
        content: str,
        allow_solution: bool,
        show_solution_banner: bool,
    ) -> str:
        """يبني عرض الحل بناءً على نية المستخدم."""
        if not allow_solution:
            return (
                "🔒 [SOLUTION HIDDEN: Student has NOT requested the solution yet.]"
                if show_solution_banner
                else ""
            )
        solution_data: dict[str, str] = {}
        for key in self.FORBIDDEN_KEYS:
            if val := item.get(key):
                solution_data[key] = str(val)
        if not solution_data:
            embedded_solutions = self._extract_solution_blocks(content)
            if embedded_solutions:
                solution_data["embedded_solution"] = "\n\n".join(embedded_solutions)
        if solution_data:
            combined_sols = "\n\n".join(
                [f"**{k.title()}**:\n{v}" for k, v in solution_data.items()]
            )
            return f"### الحل النموذجي (Official Solution):\n{combined_sols}"
        return "⚠️ [No official solution record found in database]"

    def _render_context_entry(self, sanitized_content: str, solution_display: str) -> str:
        """يعيد تمثيل نصي موحّد لكل سياق تمرين."""
        solution_section = f"\n\n{solution_display}" if solution_display else ""
        return f"**Exercise Context:**\n{sanitized_content}{solution_section}\n\n---\n"

    def _extract_solution_blocks(self, content: str) -> list[str]:
        """
        استخراج كتل الحلول المضمّنة داخل المحتوى عندما لا تتوفر حقول حل صريحة.
        """
        extracted: list[str] = []
        for pattern in self.SOLUTION_CAPTURE_PATTERNS:
            for match in re.finditer(pattern, content, flags=re.DOTALL):
                block = match.group(0).strip()
                if block and block not in extracted:
                    extracted.append(block)

        return extracted
