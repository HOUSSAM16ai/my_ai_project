"""
سير عمل الرسم البياني لوكيل التخطيط (LangGraph Workflow).

يحدد آلة الحالة لتوليد الخطط، نقدها، وتحسينها.
"""

import ast
import logging
from typing import TypedDict

from langgraph.graph import END, StateGraph

from microservices.planning_agent.cognitive import PlanCritic, PlanGenerator
from microservices.planning_agent.retrieval import rerank_context

logger = logging.getLogger("planning-agent")


class PlanningState(TypedDict):
    """تعريف الحالة للرسم البياني للتخطيط."""

    goal: str
    context: list[str]
    plan: list[str]
    score: float
    feedback: str
    iterations: int


def retrieve_node(state: PlanningState) -> dict:
    """يحسن السياق باستخدام LlamaIndex/Reranking."""
    logger.info("جاري استرجاع/إعادة ترتيب السياق...")
    # إعادة الترتيب فقط إذا لم يتم ذلك أو لضمان الجودة
    refined_ctx = rerank_context(state["goal"], state.get("context", []))
    return {"context": refined_ctx}


def generate_node(state: PlanningState) -> dict:
    """يولد خطة باستخدام DSPy."""
    logger.info(f"جاري توليد الخطة (التكرار {state.get('iterations', 0) + 1})...")

    generator = PlanGenerator()

    # إذا كان هناك ملاحظات من تكرار سابق، أضفها للسياق
    current_context = state.get("context", [])[:]
    if state.get("feedback"):
        current_context.append(f"ملاحظات الناقد: {state['feedback']}")

    try:
        pred = generator(goal=state["goal"], context=current_context)
        raw_steps = pred.plan_steps

        # تحليل قوي (Robust parsing)
        if isinstance(raw_steps, list):
            steps = raw_steps
        elif isinstance(raw_steps, str):
            try:
                clean = (
                    raw_steps.replace("```json", "")
                    .replace("```", "")
                    .replace("python", "")
                    .strip()
                )
                steps = ast.literal_eval(clean)
                if not isinstance(steps, list):
                    steps = [line.strip() for line in clean.split("\n") if line.strip()]
            except Exception:
                steps = [line.strip() for line in raw_steps.split("\n") if line.strip()]
        else:
            steps = [str(raw_steps)]

    except Exception as e:
        logger.error(f"فشل التوليد: {e}")
        steps = ["خطأ في توليد الخطة", "يرجى المحاولة مرة أخرى"]

    return {"plan": steps, "iterations": state.get("iterations", 0) + 1}


def critique_node(state: PlanningState) -> dict:
    """ينقد الخطة باستخدام DSPy."""
    logger.info("جاري نقد الخطة...")

    critic = PlanCritic()
    try:
        pred = critic(goal=state["goal"], plan_steps=state["plan"])

        # تحليل الدرجة
        try:
            raw_score = str(pred.score).split("/")[0].lower().replace("score:", "").strip()
            score = float(raw_score)
        except Exception:
            score = 5.0  # درجة افتراضية

        feedback = str(pred.feedback)
    except Exception as e:
        logger.error(f"فشل النقد: {e}")
        score = 0.0
        feedback = "خطأ أثناء النقد."

    logger.info(f"الدرجة: {score}, الملاحظات: {feedback}")
    return {"score": score, "feedback": feedback}


def should_continue(state: PlanningState):
    """يقرر ما إذا كان يجب التحسين أو الإنهاء."""
    # إذا كانت الدرجة جيدة (>= 7.0) أو وصلنا للحد الأقصى (3)، توقف.
    if state.get("score", 0) >= 7.0 or state.get("iterations", 0) >= 3:
        return END
    return "generate"


# بناء الرسم البياني
workflow = StateGraph(PlanningState)

workflow.add_node("retrieve", retrieve_node)
workflow.add_node("generate", generate_node)
workflow.add_node("critique", critique_node)

workflow.set_entry_point("retrieve")

workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", "critique")

workflow.add_conditional_edges("critique", should_continue, {END: END, "generate": "generate"})

graph = workflow.compile()
