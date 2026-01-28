"""
Writer Node ("The Luxurious Simplification").
--------------------------------------------
Orchestrates the final response generation using a Strategy Pattern
to handle Student Intent, Context Firewalling, and Adaptive Prompting.
"""

import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any

from langchain_core.messages import AIMessage

from app.core.ai_gateway import AIClient
from app.services.chat.graph.state import AgentState

# --- 1. Domain Models ---


class WriterIntent(Enum):
    GENERAL_INQUIRY = auto()
    SOLUTION_REQUEST = auto()


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
    NEGATION_PATTERN = r"(don't|do not|not|no|never|لا|ما|لم|لن|ليس).{0,20}(want|need|give|show|أريد|بدي|تعطيني|عطيني|هات)"

    @classmethod
    def analyze(cls, user_message: str) -> WriterIntent:
        msg_lower = user_message.lower()

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

    # Aggressive patterns to detect solution blocks embedded in content
    # These look for a solution header/label and match until the next Exercise/Question/Header or End of String.
    SOLUTION_PATTERNS = [
        r"(?i)\n(#{1,3}\s*(Solution|Answer|Correction|Marking Scheme|Key|الحل|الإجابة|الجواب|تصحيح|مفتاح))[\s\S]+?(?=\n(#{1,3}|Exercise|Question|السؤال|تمرين)|$)",
        r"(?i)\n(Solution|Answer|الحل|الجواب):\s*[\s\S]+?(?=\n(#{1,3}|Exercise|Question|السؤال|تمرين)|$)",
    ]

    @classmethod
    def compose(cls, search_results: list[dict[str, Any]], intent: WriterIntent) -> str:
        if not search_results:
            return ""

        context_text = ""
        for item in search_results:
            # 1. Base Content Extraction
            content = item.get("content", "")

            # 2. Field-Level Firewall
            # If user didn't ask for solution, we STRICTLY exclude known solution fields
            solution_data = {}
            if intent == WriterIntent.SOLUTION_REQUEST:
                # Retrieve all potential solution fields
                for key in cls.FORBIDDEN_KEYS:
                    if val := item.get(key):
                        solution_data[key] = val
            else:
                # Sanitization Mode: Scrub content
                content = cls._sanitize_content(content)

            # 3. Assemble Display
            solution_display = ""
            if intent == WriterIntent.SOLUTION_REQUEST:
                # Format available solution data
                if solution_data:
                    combined_sols = "\n\n".join([f"**{k.title()}**:\n{v}" for k, v in solution_data.items()])
                    solution_display = f"### الحل النموذجي (Official Solution):\n{combined_sols}"
                else:
                    solution_display = "⚠️ [No official solution record found in database]"
            else:
                solution_display = "🔒 [SOLUTION HIDDEN: Student has NOT requested the solution yet.]"

            context_text += f"**Exercise Context:**\n{content}\n\n{solution_display}\n\n---\n"

        return context_text

    @classmethod
    def _sanitize_content(cls, content: str) -> str:
        """
        Removes embedded solution blocks from the content string using Regex.
        """
        sanitized = content
        replacement = "\n\n🔒 [HIDDEN: Potential Solution Segment Redacted from Content]\n"

        for pattern in cls.SOLUTION_PATTERNS:
            # DOTALL matches newlines, allowing us to catch multi-line solution blocks if we refined regex
            # For now, we target specific headers to end of string or next block
            # Note: The simple regex provided above matches to end of string '$' which is aggressive but safe for 'leak' prevention
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.DOTALL)

        return sanitized


# --- 4. Prompt Strategist (The Pedagogical Engine) ---


class PromptStrategist:
    """
    Constructs the 'Overmind' System Prompt based on the student's level
    and the detected intent (Dual Mode vs Standard Mode).
    """

    @staticmethod
    def build_prompt(profile: StudentProfile) -> str:
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

        level_guidance = {
            "Beginner": "   - بسّط المفاهيم لأقصى درجة، استخدم تشبيهات من الواقع، وفكك المصطلحات المعقدة.",
            "Average": "   - ركز على توضيح الخطوات الصعبة والربط بين الأفكار.",
            "Advanced": "   - ناقش طرقاً بديلة، ركز على السرعة، وتحدى الطالب بأسئلة عميقة.",
        }

        return (
            base_prompt
            + dual_mode_instructions
            + level_guidance.get(profile.level, "")
            + "\n\nحافظ على نبرة فاخرة، مشجعة، واحترافية."
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
    system_prompt = PromptStrategist.build_prompt(profile)

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
