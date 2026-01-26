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

    @staticmethod
    def compose(search_results: list[dict[str, Any]], intent: WriterIntent) -> str:
        if not search_results:
            return ""

        context_text = ""
        for item in search_results:
            content = item.get("content", "")
            original_solution = item.get("solution", "")

            # Smart Solution Hiding
            if intent == WriterIntent.SOLUTION_REQUEST:
                solution_display = f"### الحل النموذجي (Official Solution):\n{original_solution}"
            else:
                solution_display = (
                    "🔒 [SOLUTION HIDDEN: Student has NOT requested the solution yet.]"
                )

            context_text += f"**Exercise Context:**\n{content}\n\n{solution_display}\n\n---\n"

        return context_text


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
            "1. **احترام السياق**: إذا كان الحل مخفياً (HIDDEN)، لا تقم بتسريبه أبداً إلا إذا طلب الطالب ذلك بوضوح.\n"
            "2. **الدقة الأكاديمية**: التزم بالمصطلحات العلمية الدقيقة.\n"
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
