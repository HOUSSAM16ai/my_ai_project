import re
from typing import ClassVar

from app.core.interfaces import IContextComposer
from app.services.chat.graph.domain import WriterIntent


class FirewallContextComposer(IContextComposer):
    """
    Formats the retrieved search results into a clean Markdown context,
    applying the 'Context Firewall' to hide solutions when not requested.
    """

    FORBIDDEN_KEYS: ClassVar[set[str]] = {
        "solution",
        "answer",
        "marking_scheme",
        "correction",
        "key",
        "answer_key",
        "solution_md",
    }
    SOLUTION_NODE_TYPES: ClassVar[set[str]] = {
        "solution",
        "answer",
        "marking_scheme",
        "key",
        "correction",
    }

    # Aggressive patterns to detect solution blocks embedded in content
    SOLUTION_PATTERNS: ClassVar[list[str]] = [
        r"(?i)\n(#{1,3}\s*(Solution|Answer|Correction|Marking Scheme|Key|الحل|الإجابة|الجواب|تصحيح|مفتاح))[\s\S]+?(?=\n\s*\*{0,2}(#{1,3}|Exercise|Question|السؤال|تمرين|التمرين)|$)",
        r"(?i)\n(Solution|Answer|الحل|الجواب):\s*[\s\S]+?(?=\n\s*\*{0,2}(#{1,3}|Exercise|Question|السؤال|تمرين|التمرين)|$)",
        r"(?is)\n\[(sol|solution):[^\]]+\][\s\S]+?(?=\n\s*\[(ex|exercise):|$)",
        r"(?i)\n\s*\*{0,2}حل\s+التمرين[\s\S]+?(?=\n\s*\*{0,2}(#{1,3}|Exercise|Question|السؤال|تمرين|التمرين)|$)",
    ]
    SOLUTION_CAPTURE_PATTERNS: ClassVar[list[str]] = [
        r"(?is)\n\[(sol|solution):[^\]]+\][\s\S]+?(?=\n\s*\[(ex|exercise):|$)",
        r"(?is)\n\s*\*{0,2}حل\s+التمرين[\s\S]+?(?=\n\s*\*{0,2}(#{1,3}|Exercise|Question|السؤال|تمرين|التمرين)|$)",
    ]

    def compose(
        self,
        search_results: list[dict[str, object]],
        intent: WriterIntent,
        user_message: str,
    ) -> str:
        if not search_results:
            return ""

        allow_solution, show_hidden_marker = self._derive_intent_flags(intent)
        context_text = ""
        for item in search_results:
            node_type = str(item.get("type", "")).lower()
            if not allow_solution and node_type in self.SOLUTION_NODE_TYPES:
                continue

            content = str(item.get("content", ""))
            content = self._extract_requested_segment(content, user_message)
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

    def _extract_requested_segment(self, content: str, user_message: str) -> str:
        """
        يقتطع جزءاً محدداً من التمرين عند طلب سؤال أو جزء بعينه.
        """
        # 1. Try extracting by Question Number
        q_idx = _extract_requested_index(user_message, ["Question", "Exercise", "السؤال", "التمرين"])

        # 2. Try extracting by Part Number
        p_idx = _extract_requested_index(user_message, ["Part", "الجزء"])

        current_content = content

        # Apply Question Filter
        if q_idx is not None:
             extracted_q = _extract_section_by_index(
                 current_content,
                 q_idx,
                 ["Question", "Exercise", "السؤال", "التمرين"]
             )
             if extracted_q:
                 current_content = extracted_q

        # Apply Part Filter (on the result of Question Filter)
        if p_idx is not None:
             extracted_p = _extract_section_by_index(
                 current_content,
                 p_idx,
                 ["Part", "الجزء", "partie"]
             )
             if extracted_p:
                 current_content = extracted_p

        return current_content


def _extract_requested_index(user_message: str, keywords: list[str]) -> int | None:
    """
    استخراج رقم السؤال أو الجزء المطلوب من رسالة المستخدم.
    """
    keywords_pattern = "|".join([re.escape(k) for k in keywords])
    pattern = re.compile(
        rf"({keywords_pattern})\s*(?:رقم|number)?\s*"
        r"(\d+|[٠-٩]+|الأول|أول|اول|الثاني|ثاني|الثالث|ثالث|الرابع|رابع|الخامس|خامس|"
        r"السادس|سادس|السابع|سابع|الثامن|ثامن|التاسع|تاسع|العاشر|عاشر|"
        r"first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)",
        re.IGNORECASE,
    )
    match = pattern.search(user_message)
    if not match:
        return None
    return _normalize_index_token(match.group(2))


def _extract_section_by_index(content: str, index: int, headers: list[str]) -> str | None:
    """
    استخراج مقطع محدد من المحتوى اعتماداً على العناوين.
    """
    headers_pattern = "|".join([re.escape(h) for h in headers])

    # REGEX to find the start of the section
    heading_regex = (
        r"(?im)^\s*(?:#{1,6}\s*)?(" + headers_pattern + r")\s*(?:رقم|number)?\s*"
        r"(\d+|[٠-٩]+|الأول|أول|اول|الثاني|ثاني|الثالث|ثالث|الرابع|رابع|الخامس|خامس|"
        r"السادس|سادس|السابع|سابع|الثامن|ثامن|التاسع|تاسع|العاشر|عاشر|"
        r"first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth)\b"
    )

    matches = list(re.finditer(heading_regex, content))
    if not matches:
        return None

    sections: list[tuple[int, int, int]] = []
    for idx, match in enumerate(matches):
        start = match.start()
        next_match_start = matches[idx + 1].start() if idx + 1 < len(matches) else len(content)
        end = next_match_start

        token_str = match.group(2)
        token_value = _normalize_index_token(token_str)
        if token_value is None:
            token_value = idx + 1

        sections.append((token_value, start, end))

    # Pattern for ANY significant header to stop at
    # SIMPLIFIED: Any line starting with a header word.
    stop_pattern = r"(?im)^\s*(?:#{1,6}\s*)?(?:Question|Exercise|Part|Section|السؤال|التمرين|الجزء|partie)\b"

    def clean_segment(segment: str, header_match: re.Match) -> str:
        """Helper to truncate segment at the next header."""
        header_end = header_match.end()
        # Search rest of segment for a stop token
        rest = segment[header_end:]
        stop_match = re.search(stop_pattern, rest)
        if stop_match:
            # Found another header, cut here
            real_end = header_end + stop_match.start()
            return segment[:real_end].strip()
        return segment.strip()

    # Find the requested section
    target_section = None
    target_start = 0

    # Try to find explicit match by value
    for token_value, start, end in sections:
        if token_value == index:
            target_section = content[start:end]
            target_start = start
            break

    # Fallback
    if target_section is None and 0 < index <= len(sections):
        _, start, end = sections[index - 1]
        target_section = content[start:end]
        target_start = start

    if target_section:
        # Match the header again to determine where the body text starts
        header_match = re.match(heading_regex, target_section)

        if header_match:
            is_question_extraction = "Question" in headers or "السؤال" in headers
            is_part_extraction = "Part" in headers or "الجزء" in headers

            # 1. Clean using Stop Tokens (truncate at next header)
            cleaned = clean_segment(target_section, header_match)

            # 2. Logic Check:
            # If we extracted "Question 1", but it was cut short because "Part 1" appeared...
            # We want to INCLUDE "Part 1" inside "Question 1".
            # `clean_segment` stops at ANY header (including Part).

            if is_question_extraction:
                 # If we are extracting Question, we should NOT stop at Part.
                 # We should only stop at Question/Exercise.
                 # Re-run logic with a specific stop pattern for Questions.

                 question_stop_pattern = r"(?im)^\s*(?:#{1,6}\s*)?(?:Question|Exercise|السؤال|التمرين)\b"

                 header_end = header_match.end()
                 rest = target_section[header_end:]
                 stop_match = re.search(question_stop_pattern, rest)

                 if stop_match:
                     real_end = header_end + stop_match.start()
                     return target_section[:real_end].strip()
                 return target_section.strip()

            elif is_part_extraction:
                # If extracting Part, we should stop at Part OR Question
                # `clean_segment` does this correctly.
                return cleaned.strip()

            return cleaned.strip()

        return target_section.strip()

    return None


def _normalize_index_token(token: str | None) -> int | None:
    """
    تحويل تمثيل الرقم (عربي/إنجليزي) إلى قيمة عددية.
    """
    if not token:
        return None
    normalized = token.strip().lower()

    # 1. Arabic/Western Digits
    arabic_digits = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
    numeric_candidate = normalized.translate(arabic_digits)
    if numeric_candidate.isdigit():
        return int(numeric_candidate)

    # 2. Textual Ordinals
    arabic_ordinals = {
        "الأول": 1, "اول": 1, "أول": 1,
        "الثاني": 2, "ثاني": 2,
        "الثالث": 3, "ثالث": 3,
        "الرابع": 4, "رابع": 4,
        "الخامس": 5, "خامس": 5,
        "السادس": 6, "سادس": 6,
        "السابع": 7, "سابع": 7,
        "الثامن": 8, "ثامن": 8,
        "التاسع": 9, "تاسع": 9,
        "العاشر": 10, "عاشر": 10,
    }
    if normalized in arabic_ordinals:
        return arabic_ordinals[normalized]

    english_ordinals = {
        "first": 1, "second": 2, "third": 3, "fourth": 4, "fifth": 5,
        "sixth": 6, "seventh": 7, "eighth": 8, "ninth": 9, "tenth": 10,
    }
    return english_ordinals.get(normalized)
