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
Your goal is to manage the workflow to provide the best possible answer to the student.

**Your Workers:**
1. **Planner**: Decomposes complex requests into a step-by-step plan.
2. **Researcher**: Searches for information, exercises, or facts.
3. **SuperReasoner**: Solves complex logical/mathematical problems deeply.
4. **ProceduralAuditor**: Specialized agent for fraud detection, conflict of interest, and compliance verification (Knowledge Graph).
5. **Writer**: Drafts the final response based on gathered information.
6. **Reviewer**: Critiques the Writer's draft for accuracy and quality.

**Workflow Guidelines:**
- **New Request**: If there is no plan, call **Planner**.
- **Execution**: If a plan exists, execute the next logical step (**Researcher** for data, **SuperReasoner** for logic, **ProceduralAuditor** for fraud/compliance).
- **Fraud/Audit**: If the user asks to check for fraud, verify relationships, or audit a process, call **ProceduralAuditor**.
- **Drafting**: Once sufficient information is gathered, call **Writer**.
- **Quality Control**: ALWAYS send the Writer's draft to **Reviewer** before finishing.
- **Correction**: If **Reviewer** gives a low score (< 8.0) or rejects the draft, you MUST send it back to **Writer** (to fix) or **Researcher** (if data was missing), with instructions.
- **Completion**: If **Reviewer** approves (score >= 8.0), choose **FINISH**.

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
            # Fallback logic if LLM fails
            if not plan:
                return {"next": "planner", "supervisor_instruction": "Fallback: Create a plan."}
            return {"next": "writer", "supervisor_instruction": "Fallback: Write response."}


async def supervisor_node(state: AgentState, ai_client: AIClient) -> dict:
    """
    غلاف (Wrapper) لعقدة المشرف ليتم استدعاؤها داخل LangGraph.
    """
    return await SupervisorNode.decide_next_step(state, ai_client)
