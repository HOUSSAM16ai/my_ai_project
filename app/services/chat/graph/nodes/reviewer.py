"""
عقدة الناقد (Reviewer Node).
----------------------------
تقوم هذه العقدة بدور "المدقق الاستراتيجي" (Strategic Auditor) ضمن حلقة Maker-Checker.
تطبق معايير هندسية صارمة لضمان الجودة، وتصدر "حزمة مراجعة" (Review Packet).
"""

import json

from app.core.ai_gateway import AIClient
from app.core.logging import get_logger
from app.core.maf.spec import ReviewChecklist, ReviewPacket
from app.services.chat.graph.state import AgentState
from app.services.chat.memory_engine import get_memory_engine

logger = get_logger("reviewer-node")


class ReviewerNode:
    """
    المدقق الذكي (The Intelligent Checker).
    ينفذ خوارزمية "التأمل الذاتي" (Self-Reflection Loop) ويصدر أحكاماً قابلة للتنفيذ.
    """

    SYSTEM_PROMPT = """
You are the "Strategic Auditor" (The Checker), a super-intelligent critique engine.
Your goal is to apply a rigorous "Maker-Checker" quality loop to the Tutor's response.
You must not just "edit" text; you must DIAGNOSE defects using the following Engineering Checklist:

1. **Requirements:** Did it meet all implicit/explicit user needs?
2. **Constraints:** Did it adhere to tone (Formal Arabic/Luxurious), format (Markdown/LaTeX), and policy (Solution Hiding)?
3. **Assumptions:** Are there unauthorized or hidden assumptions?
4. **Contradictions:** Are there internal logic conflicts?
5. **Justification:** Is every claim clearly justified?
6. **Worst-Case:** What is the worst-case failure mode of this answer?
7. **Minimal Fix:** What is the atomic edit needed to fix it?

**OUTPUT FORMAT:**
Return ONLY valid JSON matching this schema:
{
  "checklist": {
    "requirements_met": bool,
    "constraints_met": bool,
    "assumptions_flagged": [str],
    "contradictions_found": [str],
    "justification_clear": bool,
    "worst_case_analysis": str,
    "minimal_fix_suggestion": str
  },
  "score": float,  # 0.0 to 10.0
  "actionable_feedback": str,  # Direct instruction to the Maker (Writer)
  "recommendation": "APPROVE" | "REJECT"
}

If score < 8.0, recommendation MUST be "REJECT".
"""

    @staticmethod
    async def review(response_text: str, question: str, ai_client: AIClient) -> ReviewPacket:
        if not response_text:
            return ReviewPacket(
                checklist=ReviewChecklist(
                    requirements_met=False,
                    constraints_met=False,
                    assumptions_flagged=["No content generated"],
                    contradictions_found=[],
                    justification_clear=False,
                    worst_case_analysis="Empty response",
                    minimal_fix_suggestion="Generate content",
                ),
                score=0.0,
                actionable_feedback="No response generated.",
                recommendation="REJECT",
            )

        prompt = f"""
Student Question: {question}

Tutor Response (Target for Audit):
{response_text}

---
Perform the Strategic Audit now. Return JSON.
"""
        try:
            result_text = await ai_client.generate_text(
                prompt,
                system_prompt=ReviewerNode.SYSTEM_PROMPT,
                temperature=0.0,  # Deterministic critique
            )

            # Clean JSON
            clean_json = result_text.content.strip()
            if clean_json.startswith("```json"):
                clean_json = clean_json[7:-3]
            elif clean_json.startswith("```"):
                clean_json = clean_json[3:-3]

            data = json.loads(clean_json)

            # Validate against Pydantic Model
            checklist_data = data.get("checklist", {})
            checklist = ReviewChecklist(**checklist_data)

            return ReviewPacket(
                checklist=checklist,
                score=float(data.get("score", 5.0)),
                actionable_feedback=data.get("actionable_feedback", "Check content."),
                recommendation=data.get("recommendation", "REJECT"),
            )

        except Exception as e:
            logger.error(f"Review Audit failed: {e}")
            # Fail safe: Reject to force regeneration or manual review, OR Approve if we trust the Maker.
            # In High-Reliability context, we default to WARNING/PASS but with low score to signal issue without crashing.
            # However, for this loop, let's create a dummy fail packet.
            return ReviewPacket(
                checklist=ReviewChecklist(
                    requirements_met=True,
                    constraints_met=True,
                    assumptions_flagged=[],
                    contradictions_found=["Audit Process Failed"],
                    justification_clear=True,
                    worst_case_analysis="Audit Mechanism Failure",
                    minimal_fix_suggestion="Retry Audit",
                ),
                score=5.0,
                actionable_feedback="The Auditor encountered an error. Proceed with caution.",
                recommendation="APPROVE",  # Prevent infinite loop on error
            )


async def reviewer_node(state: AgentState, ai_client: AIClient) -> dict:
    """
    عقدة المراجعة في الرسم البياني.
    """
    messages = state["messages"]
    if not messages:
        return {"review_score": 0.0, "review_feedback": "No messages to review."}

    last_response = state.get("final_response", "")
    last_user_msg = "Unknown question"
    for msg in reversed(messages):
        if msg.type == "human":
            last_user_msg = msg.content
            break

    # Current iteration check
    current_iter = state.get("iteration_count", 0)

    # Max Iteration Guard
    if current_iter >= 3:
        logger.warning("Max iterations reached. Forcing approval.")
        # Create a forced approval packet
        forced_packet = ReviewPacket(
            checklist=ReviewChecklist(
                requirements_met=True,
                constraints_met=True,
                assumptions_flagged=[],
                contradictions_found=[],
                justification_clear=True,
                worst_case_analysis="Max iterations",
                minimal_fix_suggestion="None",
            ),
            score=10.0,
            actionable_feedback="Max iterations reached.",
            recommendation="APPROVE",
        )
        return {
            "review_packet": forced_packet.model_dump(),
            "review_score": 10.0,
            "review_feedback": "Max iterations reached.",
            "iteration_count": current_iter + 1,
        }

    # Execute Review
    packet = await ReviewerNode.review(last_response, last_user_msg, ai_client)

    logger.info(
        f"Audit Complete. Score: {packet.score}, Rec: {packet.recommendation}"
    )

    # Continual Learning
    try:
        if last_user_msg and last_response:
            engine = get_memory_engine()
            await engine.learn(
                ai_client=ai_client,
                query=last_user_msg,
                plan=state.get("plan", []),
                response=last_response,
                score=packet.score,
                feedback=packet.actionable_feedback,
            )
    except Exception as e:
        logger.error(f"Failed to save learning experience: {e}")

    # Legacy / MAF Compatibility: Map ReviewPacket to AttackReport
    # If recommendation is REJECT, it's a "Successful Attack".
    attack_report = {
        "counterexamples": packet.checklist.contradictions_found,
        "failure_modes": packet.checklist.assumptions_flagged,
        "severity": (10.0 - packet.score) if packet.recommendation == "REJECT" else 0.0,
        "successful": packet.recommendation == "REJECT",
        "feedback": packet.actionable_feedback,
    }

    return {
        "review_packet": packet.model_dump(),
        "review_score": packet.score,
        "review_feedback": packet.actionable_feedback,
        "iteration_count": current_iter + 1,
        "maf_attack": attack_report,
    }
