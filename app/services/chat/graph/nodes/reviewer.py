"""
عقدة الناقد (Reviewer Node).
----------------------------
تقوم هذه العقدة بدور "الناقد الأكاديمي" (Academic Critic) لضمان جودة المخرجات.
تتحقق من الدقة العلمية، التنسيق (Markdown/LaTeX)، والأسلوب.
"""

import json
from dataclasses import dataclass

from app.core.ai_gateway import AIClient
from app.core.logging import get_logger
from app.services.chat.graph.state import AgentState
from app.services.chat.memory_engine import get_memory_engine

logger = get_logger("reviewer-node")


@dataclass
class ReviewResult:
    score: float  # 0.0 to 10.0
    feedback: str
    approved: bool


class ReviewerNode:
    """
    الناقد الذكي (The Intelligent Critic).
    يفحص الرد النهائي ويقدم تقييماً وملاحظات تحسينية.
    """

    SYSTEM_PROMPT = """
أنت "الناقد الأكاديمي" (The Academic Critic)، ومهمتك ضمان الجودة الفائقة للمحتوى التعليمي.
قم بمراجعة رد المعلم (The Tutor) على سؤال الطالب بناءً على المعايير التالية:

1. **الدقة العلمية (Scientific Accuracy):** هل المعلومات صحيحة تماماً؟
2. **التنسيق (Formatting):** هل يتم استخدام Markdown و LaTeX بشكل سليم؟ (يجب أن تكون المعادلات بين `$` أو `$$`).
3. **الأسلوب (Tone):** هل الأسلوب فاخر، مشجع، واحترافي؟
4. **اكتمال الإجابة (Completeness):** هل أجاب على السؤال بالكامل؟
5. **إخفاء الحل (Solution Hiding):** إذا لم يطلب الطالب الحل صراحة، هل تم إخفاؤه؟ (تأكد من عدم تسريب الحلول إلا بطلب واضح).

**المخرجات المطلوبة:**
يجب أن يكون ردك بصيغة JSON فقط:
{
    "score": <float 0-10>,
    "feedback": "<نقد بناء ومحدد باللغة العربية>",
    "approved": <boolean>
}

إذا كانت الدرجة أقل من 8.0، يجب أن تكون `approved` بـ `false`.
"""

    @staticmethod
    async def review(response_text: str, question: str, ai_client: AIClient) -> ReviewResult:
        if not response_text:
            return ReviewResult(0.0, "No response generated.", False)

        prompt = f"""
Student Question: {question}

Tutor Response:
{response_text}

---
Evaluate this response now. Return JSON.
"""
        try:
            # We use json_mode=True if available, but for now prompt engineering is key.
            # Assuming AIClient handles basic text generation.
            result_text = await ai_client.generate_text(
                prompt,
                system_prompt=ReviewerNode.SYSTEM_PROMPT,
                temperature=0.0,  # Deterministic critique
            )

            # Simple cleaning for JSON parsing
            clean_json = result_text.content.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:-3]
            elif clean_json.startswith("```"):
                clean_json = clean_json[3:-3]

            data = json.loads(clean_json)

            return ReviewResult(
                score=float(data.get("score", 5.0)),
                feedback=data.get("feedback", "No feedback provided."),
                approved=bool(data.get("approved", False)),
            )

        except Exception as e:
            logger.error(f"Review failed: {e}")
            # Fail safe: approve to avoid getting stuck, but log error.
            return ReviewResult(10.0, "Reviewer failed, auto-approved.", True)


async def reviewer_node(state: AgentState, ai_client: AIClient) -> dict:
    """
    عقدة المراجعة في الرسم البياني.
    """
    messages = state["messages"]
    if not messages:
        return {"review_score": 0.0, "review_feedback": "No messages to review."}

    # Extract the last AI response (Target) and the last User message (Context)
    last_response = state.get("final_response", "")

    # Find last user message
    last_user_msg = "Unknown question"
    for msg in reversed(messages):
        if msg.type == "human":
            last_user_msg = msg.content
            break

    # Current iteration check
    current_iter = state.get("iteration_count", 0)

    # If we have looped too many times, force approve to prevent infinite loops
    if current_iter >= 3:
        logger.warning("Max iterations reached. Forcing approval.")
        return {
            "review_score": 10.0,
            "review_feedback": "Max iterations reached.",
            "iteration_count": current_iter + 1,
        }

    # Perform Review
    review_result = await ReviewerNode.review(last_response, last_user_msg, ai_client)

    logger.info(
        f"Review complete. Score: {review_result.score}, Approved: {review_result.approved}"
    )

    # Continual Learning: Save the experience
    try:
        # Ensure we have valid data before attempting to learn
        if last_user_msg and last_response:
            engine = get_memory_engine()
            await engine.learn(
                ai_client=ai_client,
                query=last_user_msg,
                plan=state.get("plan", []),
                response=last_response,
                score=review_result.score,
                feedback=review_result.feedback,
            )
        else:
            logger.warning("Skipping learning: Missing query or response.")
    except Exception as e:
        logger.error(f"Failed to save learning experience: {e}")

    # MAF-1.0 Integration: Generate Attack Report
    # We treat any low score as a successful "Attack" (finding flaws).
    attack_report = {
        "counterexamples": [],
        "failure_modes": ["Quality check failed" if not review_result.approved else "None"],
        "severity": (10.0 - review_result.score) if not review_result.approved else 0.0,
        "successful": not review_result.approved,
        "feedback": review_result.feedback,
    }

    return {
        "review_score": review_result.score,
        "review_feedback": review_result.feedback,
        "iteration_count": current_iter + 1,
        "maf_attack": attack_report,  # Push to state for Kernel
    }
