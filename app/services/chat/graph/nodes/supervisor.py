"""
عقدة المشرف الذكي (Smart Supervisor Node).
-----------------------------------------
يعمل هذا المشرف كـ "قائد الأوركسترا" (Orchestrator)، حيث يستخدم الذكاء الاصطناعي
لتحديد الخطوة التالية ديناميكيًا بناءً على حالة المحادثة وجودة المخرجات.
"""

import json
import logging

from app.core.ai_gateway import AIClient
from app.services.chat.graph.state import AgentState

logger = logging.getLogger(__name__)


class SupervisorNode:
    """
    المشرف الذكي (The Intelligent Supervisor).
    يوزع المهام على الوكلاء المتخصصين ويراقب الجودة.
    """

    SYSTEM_PROMPT = """
You are the **Supervisor Agent** (Orchestrator) of an advanced educational AI system.
Your goal is to manage the workflow to provide the "Legendary Quality" answer to the student or admin.

**Your Workers:**
1. **Planner**: Decomposes complex requests into a step-by-step plan.
2. **Researcher**: Searches for information, exercises, or facts.
3. **SuperReasoner**: Solves complex logical/mathematical problems deeply.
4. **ProceduralAuditor**: Specialized agent for fraud detection, conflict of interest, and compliance verification (Knowledge Graph).
5. **Writer**: Drafts the final response based on gathered information.
6. **Reviewer**: Critiques the Writer's draft for accuracy and quality.

**Decision Logic (The "Super" Protocol):**
1. **COMPLEXITY CHECK**: Is the user asking a complex question, a math problem, or an admin query requiring deep analysis?
   - **YES**: Route to **SuperReasoner** (for logic) or **Researcher** (for data) first. NEVER route directly to Writer unless the context is already populated.
   - **NO** (Simple greeting/thanks): Route to **Writer**.

2. **AUDIT CHECK**: Does the user mention fraud, compliance, or "check this"?
   - **YES**: Route to **ProceduralAuditor**.

3. **WRITING PHASE**: Once information is gathered (from Reasoner/Researcher):
   - Route to **Writer**.
   - **CRITICAL**: You MUST provide this instruction to the Writer: "Synthesize the Reasoning/Research findings into a Legendary Professional Arabic response. Ensure deep analysis."

4. **REVIEW PHASE**: ALWAYS send the Writer's draft to **Reviewer** before finishing.
   - If **Reviewer** rejects (< 8.0), send back to **Writer** with the feedback.
   - If **Reviewer** approves, choose **FINISH**.

**Input Context:**
- **Last Message**: The latest output from a worker or user.
- **Plan**: Current plan steps.
- **Review**: Last review score and feedback (if any).

**Output Format:**
You must return a JSON object ONLY:
{
    "next": "<worker_name_or_FINISH>",
    "instruction": "<specific_instruction_for_the_worker>",
    "reason": "<why_you_chose_this>"
}

Valid `next` values: `planner`, `researcher`, `super_reasoner`, `procedural_auditor`, `writer`, `reviewer`, `FINISH`.
"""

    @staticmethod
    async def decide_next_step(state: AgentState, ai_client: AIClient) -> dict:
        """
        يقرر الخطوة التالية باستخدام LLM.
        """
        messages = state.get("messages", [])
        last_message = messages[-1].content if messages else "No history."

        # Prepare Context
        plan = state.get("plan", [])
        current_step = state.get("current_step_index", 0)
        review_score = state.get("review_score")
        review_feedback = state.get("review_feedback")

        context_str = f"""
--- CURRENT STATE ---
Last Message: {last_message[:500]}... (truncated)
Current Plan: {plan}
Current Step Index: {current_step}
Last Review Score: {review_score}
Last Review Feedback: {review_feedback}
---------------------

Based on the above, what is the next step?
"""

        try:
            response = await ai_client.send_message(
                system_prompt=SupervisorNode.SYSTEM_PROMPT, user_message=context_str
            )

            # Clean JSON
            clean_content = response.replace("```json", "").replace("```", "").strip()

            try:
                decision = json.loads(clean_content)
            except json.JSONDecodeError:
                # PERCEPTION-ACTION LOOP REPAIR: Self-Correction
                # If the agent failed to produce valid JSON, we feed the error back to it (Feedback Loop).
                logger.warning("Supervisor produced invalid JSON. Retrying with feedback...")
                retry_context = f"{context_str}\n\nERROR: Your previous response was not valid JSON:\n{clean_content}\n\nFIX: Return ONLY valid JSON."

                response = await ai_client.send_message(
                    system_prompt=SupervisorNode.SYSTEM_PROMPT, user_message=retry_context
                )
                clean_content = response.replace("```json", "").replace("```", "").strip()
                decision = json.loads(clean_content)

            next_node = decision.get("next", "FINISH")
            instruction = decision.get("instruction", "")
            reason = decision.get("reason", "")

            logger.info(f"Supervisor Decision: {next_node} | Reason: {reason}")

            return {
                "next": next_node,
                "supervisor_instruction": instruction,
                "routing_trace": [{"node": next_node, "reason": reason}],
            }

        except Exception as e:
            logger.error(f"Supervisor logic failed: {e}")
            # Intelligent Fallback
            # If we have no plan, we MUST plan.
            if not plan:
                return {
                    "next": "planner",
                    "supervisor_instruction": "Fallback: System error, please create a recovery plan.",
                }

            # If we are deep in the process, go to writer but warn them.
            return {
                "next": "writer",
                "supervisor_instruction": "Fallback: Supervisor encountered an error. Synthesize available information carefully.",
            }


async def supervisor_node(state: AgentState, ai_client: AIClient) -> dict:
    """
    غلاف (Wrapper) لعقدة المشرف ليتم استدعاؤها داخل LangGraph.
    """
    return await SupervisorNode.decide_next_step(state, ai_client)
