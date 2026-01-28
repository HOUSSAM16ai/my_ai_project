"""
Writer Node ("The Luxurious Simplification").
--------------------------------------------
Orchestrates the final response generation using a Strategy Pattern
to handle Student Intent, Context Firewalling, and Adaptive Prompting.
"""

import re
from dataclasses import dataclass
from enum import Enum, auto

from langchain_core.messages import AIMessage

from app.core.ai_gateway import AIClient
from app.services.chat.graph.state import AgentState

# --- 1. Domain Models ---


class WriterIntent(Enum):
    GENERAL_INQUIRY = auto()
    SOLUTION_REQUEST = auto()
    DIAGNOSIS_REQUEST = auto()
    QUESTION_ONLY_REQUEST = auto()


@dataclass
class StudentProfile:
    level: str  # Beginner, Average, Advanced


# --- 2. Intent Detector (The Genius Firewall) ---


class IntentDetector:
    """
    Analyzes user input to determine if they are explicitly requesting
    the solution (triggering Dual Mode) or just asking a general question.
    """

    # Regex patterns for high-precision detection
    REQUEST_INDICATORS = r"(أريد|بدي|ابغى|عطيني|اعطني|هات|وريني|show|give|want|provide|display|please|plz|من فضلك|لو سمحت)"
    TARGET_NOUNS = r"(حل|إجابة|اجابة|جواب|صحح|تصحيح|solution|answer|result|correction)"
    # Updated negation to include "without" variants
    NEGATION_PATTERN = r"(don't|do not|not|no|never|without|sans|لا|ما|لم|لن|ليس|بدون|بلاش|من غير).{0,20}(want|need|give|show|solution|answer|أريد|بدي|تعطيني|عطيني|هات|حل|إجابة)"
    DIAGNOSIS_KEYWORDS = r"(diagnose|quiz|test|exam|assessment|شخصني|ختبرني|إختبار|اختبار|قيم|تقييم|مراجعة)"
    QUESTION_ONLY_KEYWORDS = (
        r"(أسئلة\s*فقط|فقط\s*أسئلة|questions\s*only|just\s*questions|"
        r"بدون\s*إجابة|بدون\s*اجابة|بدون\s*حلول|بدون\s*حل|لا\s*أريد\s*الحل|"
        r"ما\s*أريد\s*الحل|لا\s*تعطيني\s*الحل|لا\s*أحتاج\s*الحل|"
        r"without\s*answers|no\s*answers|without\s*solution|no\s*solution)"
    )

    @classmethod
    def analyze(cls, user_message: str) -> WriterIntent:
        msg_lower = user_message.lower()

        # Check for Diagnosis first
        is_diagnosis = bool(re.search(cls.DIAGNOSIS_KEYWORDS, msg_lower))
        if is_diagnosis:
            return WriterIntent.DIAGNOSIS_REQUEST
        is_questions_only = bool(re.search(cls.QUESTION_ONLY_KEYWORDS, msg_lower))
        if is_questions_only:
            return WriterIntent.QUESTION_ONLY_REQUEST

        has_noun = bool(re.search(cls.TARGET_NOUNS, msg_lower))
        is_request = bool(re.search(cls.REQUEST_INDICATORS, msg_lower))
        is_question = "?" in msg_lower or "؟" in msg_lower
        is_short = len(msg_lower.split()) <= 3
        has_negation = bool(re.search(cls.NEGATION_PATTERN, msg_lower))

        # Decision Matrix
        if has_noun and not has_negation and (is_request or is_question or is_short):
            return WriterIntent.SOLUTION_REQUEST

        return WriterIntent.GENERAL_INQUIRY


# --- 3. Context Composer (The Knowledge Weaver) ---


class ContextComposer:
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
    # These look for a solution header/label and match until the next Exercise/Question/Header or End of String.
    # Updated to handle Markdown bolding (e.g. **Exercise**) and Arabic terms.
    # Note: (?s) enables DOTALL mode for the whole regex.
    # The regex matches a solution header, then greedily consumes text until it hits a Lookahead for another Exercise/Question header OR End of String.
    # We added \s* to handle spacing and \*{0,2} for markdown bolding.
    # Added "التمرين" (with Al-) to ensure Arabic headers like "**التمرين الثاني**" are detected as stop markers.
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

    @classmethod
    def compose(cls, search_results: list[dict[str, object]], intent: WriterIntent) -> str:
        if not search_results:
            return ""

        allow_solution, show_hidden_marker = cls._derive_intent_flags(intent)
        context_text = ""
        for item in search_results:
            node_type = str(item.get("type", "")).lower()
            if not allow_solution and node_type in cls.SOLUTION_NODE_TYPES:
                continue

            content = str(item.get("content", ""))
            sanitized_content = cls._sanitize_content(
                content, show_hidden_marker=show_hidden_marker
            )

            solution_display = cls._compose_solution_display(
                item=item,
                content=content,
                allow_solution=allow_solution,
                show_solution_banner=show_hidden_marker,
            )
            context_text += cls._render_context_entry(
                sanitized_content=sanitized_content, solution_display=solution_display
            )

        return context_text

    @staticmethod
    def _derive_intent_flags(intent: WriterIntent) -> tuple[bool, bool]:
        """يشتق أعلام التحكم الرئيسية من نية المستخدم."""
        allow_solution = intent == WriterIntent.SOLUTION_REQUEST
        show_hidden_marker = intent == WriterIntent.GENERAL_INQUIRY
        return allow_solution, show_hidden_marker

    @classmethod
    def _sanitize_content(cls, content: str, show_hidden_marker: bool) -> str:
        """
        إزالة مقاطع الحلول المضمّنة داخل المحتوى باستخدام التعبيرات النمطية.
        """
        sanitized = content
        replacement = (
            "\n\n🔒 [HIDDEN: Potential Solution Segment Redacted from Content]\n"
            if show_hidden_marker
            else "\n\n"
        )

        for pattern in cls.SOLUTION_PATTERNS:
            # DOTALL matches newlines, allowing us to catch multi-line solution blocks if we refined regex
            # For now, we target specific headers to end of string or next block
            # Note: The simple regex provided above matches to end of string '$' which is aggressive but safe for 'leak' prevention
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.DOTALL)

        return sanitized

    @classmethod
    def _compose_solution_display(
        cls,
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
        for key in cls.FORBIDDEN_KEYS:
            if val := item.get(key):
                solution_data[key] = str(val)
        if not solution_data:
            embedded_solutions = cls._extract_solution_blocks(content)
            if embedded_solutions:
                solution_data["embedded_solution"] = "\n\n".join(embedded_solutions)
        if solution_data:
            combined_sols = "\n\n".join(
                [f"**{k.title()}**:\n{v}" for k, v in solution_data.items()]
            )
            return f"### الحل النموذجي (Official Solution):\n{combined_sols}"
        return "⚠️ [No official solution record found in database]"

    @classmethod
    def _render_context_entry(cls, sanitized_content: str, solution_display: str) -> str:
        """يعيد تمثيل نصي موحّد لكل سياق تمرين."""
        solution_section = f"\n\n{solution_display}" if solution_display else ""
        return f"**Exercise Context:**\n{sanitized_content}{solution_section}\n\n---\n"

    @classmethod
    def _extract_solution_blocks(cls, content: str) -> list[str]:
        """
        استخراج كتل الحلول المضمّنة داخل المحتوى عندما لا تتوفر حقول حل صريحة.
        """
        extracted: list[str] = []
        for pattern in cls.SOLUTION_CAPTURE_PATTERNS:
            for match in re.finditer(pattern, content, flags=re.DOTALL):
                block = match.group(0).strip()
                if block and block not in extracted:
                    extracted.append(block)

        return extracted


# --- 4. Prompt Strategist (The Pedagogical Engine) ---


class PromptStrategist:
    """
    Constructs the 'Overmind' System Prompt based on the student's level
    and the detected intent (Dual Mode vs Standard Mode).
    """

    @staticmethod
    def build_prompt(profile: StudentProfile, intent: WriterIntent) -> str:
        base_prompt = (
            "أنت 'Overmind'، المعلم الذكي (Smart Tutor) والموجه الأكاديمي الفاخر.\n"
            "مهمتك: مساعدة الطالب باستخدام المحتوى المسترجع (Context) بذكاء وحكمة.\n\n"
            "### القواعد الذهبية (The Golden Rules):\n"
            "1. **احترام السياق (Context Firewall)**: إذا كان الحل مخفياً (HIDDEN)، **يُمنع منعاً باتاً** توليد الحل أو الإجابة أو المفتاح.\n"
            "   - **مسموح فقط**: عرض نص السؤال/التمرين وتوجيه الطالب للتفكير.\n"
            "   - **تحذير**: حتى لو رأيت الحل في النص (عن طريق الخطأ)، تجاهله تماماً ولا تذكره.\n"
            "2. **الدقة الأكاديمية**: التزم بالمصطلحات العلمية الدقيقة.\n"
            "3. **التحديد (Granularity)**: إذا طلب الطالب جزءاً محدداً (مثل 'السؤال الأول' أو 'Question 1'):\n"
            "   - **استخرج فقط** الجزء المطلوب من السياق.\n"
            "   - لا تعرض التمرين بالكامل إذا لم يُطلب منك ذلك.\n"
            "4. **التفاعل الذكي (Interactive Guardrail)**: إذا طلب الطالب تمريناً (ولم يطلب الحل صراحة):\n"
            "   - قدم التمرين فقط.\n"
            "   - اسأل الطالب في النهاية: 'هل تريد اختبار نفسك قبل أن أعطيك الحل؟' (أو صيغة مشابهة مشجعة).\n"
            "   - لا تقدم الحل أبداً في الخطوة الأولى.\n"
        )

        dual_mode_instructions = ""
        if intent == WriterIntent.SOLUTION_REQUEST:
            dual_mode_instructions = (
                "\n### بروتوكول الوضع المزدوج (Dual Mode Protocol):\n"
                "عندما يطلب الطالب الحل، يجب عليك تقديم الرد في جزأين منفصلين:\n"
                "1. **الجزء الأول (الصرامة - Official Key):**\n"
                "   - اعرض الحل النموذجي الرسمي كما هو في السياق.\n"
                "   - استخدم العنوان: `### الحل النموذجي`.\n"
                "2. **الجزء الثاني (المرونة - Supernatural Explanation):**\n"
                "   - اشرح الحل بأسلوب مبسط وعميق.\n"
                f"   - مستوى الطالب: **{profile.level}**.\n"
            )

        diagnosis_instructions = ""
        if intent == WriterIntent.DIAGNOSIS_REQUEST:
            diagnosis_instructions = (
                "\n### بروتوكول التشخيص (Diagnosis Mode):\n"
                "أنت الآن الممتحن (The Examiner). مهمتك ليست الشرح بل الاختبار.\n"
                "1. قدم السؤال/التمرين بوضوح دون أي تلميحات للإجابة.\n"
                "2. اطلب من الطالب محاولة الحل أولاً.\n"
                "3. كن مشجعاً وحازماً في نفس الوقت.\n"
            )

        question_only_instructions = ""
        if intent == WriterIntent.QUESTION_ONLY_REQUEST:
            question_only_instructions = PromptStrategist._question_only_instructions()

        level_guidance = {
            "Beginner": "   - بسّط المفاهيم لأقصى درجة، استخدم تشبيهات من الواقع، وفكك المصطلحات المعقدة.",
            "Average": "   - ركز على توضيح الخطوات الصعبة والربط بين الأفكار.",
            "Advanced": "   - ناقش طرقاً بديلة، ركز على السرعة، وتحدى الطالب بأسئلة عميقة.",
        }

        return (
            base_prompt
            + dual_mode_instructions
            + diagnosis_instructions
            + question_only_instructions
            + level_guidance.get(profile.level, "")
            + "\n\nحافظ على نبرة فاخرة، مشجعة، واحترافية."
        )

    @staticmethod
    def _question_only_instructions() -> str:
        """يبني توجيهاً صارماً عند طلب المستخدم أسئلة فقط دون إجابات."""
        return (
            "\n### بروتوكول الأسئلة فقط (Questions-Only Mode):\n"
            "1. اعرض الأسئلة أو التمارين فقط دون أي حلول أو تلميحات.\n"
            "2. امتنع تماماً عن الشرح أو الإجابة، حتى لو ظهر الحل في السياق.\n"
            "3. اختم بسؤال تشجيعي: 'هل تريد محاولة الحل أولاً أم ترغب بالإجابة لاحقاً؟'.\n"
        )


# --- 5. Main Node Orchestrator ---


async def writer_node(state: AgentState, ai_client: AIClient) -> dict:
    """
    The Orchestrator Function.
    Flow: Input -> Detect Intent -> Compose Context -> Build Prompt -> Generate.
    """
    # 1. Extraction
    messages = state["messages"]
    last_user_msg = messages[-1].content
    search_results = state.get("search_results", [])
    student_level = state.get("diagnosis", "Average")

    # 2. Analysis
    intent = IntentDetector.analyze(last_user_msg)
    profile = StudentProfile(level=student_level)

    # 3. Composition
    context_text = ContextComposer.compose(search_results, intent)
    system_prompt = PromptStrategist.build_prompt(profile, intent)

    # Inject Critique if available (The Self-Correction Loop)
    review_feedback = state.get("review_feedback")
    if review_feedback:
        system_prompt += (
            f"\n\n### CRITICAL INSTRUCTION (Correction Mode):\n"
            f"Your previous answer was rejected by the Academic Critic.\n"
            f"REWRITE IT based on this feedback:\n'{review_feedback}'\n"
            f"Ensure you address every point and maintain the luxurious tone."
        )

    # 4. Payload Construction
    final_user_content = f"Context:\n{context_text}\n\nStudent Question: {last_user_msg}"

    # 5. Execution
    final_text = await ai_client.send_message(
        system_prompt=system_prompt, user_message=final_user_content
    )

    return {
        "messages": [AIMessage(content=final_text)],
        "current_step_index": state["current_step_index"] + 1,
        "final_response": final_text,
    }
