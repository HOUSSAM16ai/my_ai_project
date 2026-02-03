"""
Writer Node ("The Luxurious Simplification").
--------------------------------------------
Orchestrates the final response generation using a Strategy Pattern
to handle Student Intent, Context Firewalling, and Adaptive Prompting.
"""

from langchain_core.messages import AIMessage, HumanMessage

from app.core.ai_gateway import AIClient
from app.core.di import Container
from app.core.interfaces import IContextComposer, IIntentDetector, IPromptStrategist
from app.core.maf.spec import ReviewPacket
from app.services.chat.graph.components.context_composer import FirewallContextComposer
from app.services.chat.graph.components.intent_detector import RegexIntentDetector
from app.services.chat.graph.components.prompt_strategist import StandardPromptStrategist
from app.services.chat.graph.domain import StudentProfile
from app.services.chat.graph.state import AgentState


def _ensure_dependencies():
    """
    Ensure dependencies are registered in the Container.
    Uses a 'Look Before You Leap' or 'Ask for Forgiveness' approach depending on Container implementation.
    Here we just re-register or register if missing.
    """
    # Note: In a real app, this should be done in a main.py or bootstrap.
    # We do it here to keep the node self-contained but avoid import-side-effects.

    try:
        if not Container.resolve(IIntentDetector):
            Container.register_singleton(IIntentDetector, RegexIntentDetector())
    except Exception:
        Container.register_singleton(IIntentDetector, RegexIntentDetector())

    try:
        if not Container.resolve(IContextComposer):
            Container.register_singleton(IContextComposer, FirewallContextComposer())
    except Exception:
        Container.register_singleton(IContextComposer, FirewallContextComposer())

    try:
        if not Container.resolve(IPromptStrategist):
            Container.register_singleton(IPromptStrategist, StandardPromptStrategist())
    except Exception:
        Container.register_singleton(IPromptStrategist, StandardPromptStrategist())


# --- Main Node Orchestrator ---


async def writer_node(state: AgentState, ai_client: AIClient) -> dict:
    """
    The Orchestrator Function.
    Flow: Input -> Detect Intent -> Compose Context -> Build Prompt -> Generate.
    Refactored to use Dependency Injection (SOLID).
    """
    # 0. Bootstrap (if needed)
    _ensure_dependencies()

    # 1. Resolve Dependencies
    intent_detector = Container.resolve(IIntentDetector)
    context_composer = Container.resolve(IContextComposer)
    prompt_strategist = Container.resolve(IPromptStrategist)

    # 2. Extraction & Smart History Parsing
    messages = state.get("messages", [])
    search_results = state.get("search_results", [])
    student_level = state.get("diagnosis", "Average")
    supervisor_instruction = state.get("supervisor_instruction", "")

    # Locate the true User Question and Gather Reasoning Traces (Chain of Thought)
    last_user_msg = ""
    reasoning_traces = []

    # Iterate backwards to find the last HumanMessage
    for msg in reversed(messages):
        if isinstance(msg, HumanMessage):
            last_user_msg = msg.content
            break
        if isinstance(msg, AIMessage) and msg.content:
            # This is output from SuperReasoner, Researcher, or ProceduralAuditor
            reasoning_traces.append(msg.content)

    # Reverse traces to maintain chronological order (Node A output -> Node B output)
    reasoning_traces.reverse()
    full_reasoning_context = "\n---\n".join(reasoning_traces)

    # Fallback if no HumanMessage found (edge case)
    if not last_user_msg and messages:
        last_user_msg = messages[-1].content

    # 3. Analysis (on the User's actual question, not the reasoning dump)
    intent = intent_detector.analyze(last_user_msg)
    profile = StudentProfile(level=student_level)

    # 4. Composition
    context_text = context_composer.compose(search_results, intent, last_user_msg)

    # Inject Reasoning Traces into Context
    if full_reasoning_context:
        context_text += f"\n\n### 🧠 DEEP REASONING & ANALYSIS (INTERNAL THOUGHTS):\n{full_reasoning_context}\n(Use this reasoning to construct the final answer, but do not just copy-paste it. Synthesize it.)"

    system_prompt = prompt_strategist.build_prompt(profile, intent)

    # Inject Supervisor Instructions (Dynamic Orchestration)
    if supervisor_instruction:
        system_prompt += (
            f"\n\n### SUPERVISOR INSTRUCTION:\n"
            f"{supervisor_instruction}\n"
            f"(You MUST strictly follow this specific instruction from your Supervisor)."
        )

    # Inject Critique if available (The Self-Correction Loop)
    review_packet_data = state.get("review_packet")

    if review_packet_data:
        try:
            packet = ReviewPacket(**review_packet_data)
            if packet.recommendation == "REJECT":
                system_prompt += (
                    f"\n\n### CRITICAL AUDIT FINDINGS (Correction Mode):\n"
                    f"Your previous output was REJECTED by the Strategic Auditor.\n"
                    f"**Actionable Feedback:** {packet.actionable_feedback}\n"
                    f"**Minimal Fix Required:** {packet.checklist.minimal_fix_suggestion}\n"
                    f"**Identified Defects:** {', '.join(packet.checklist.contradictions_found + packet.checklist.assumptions_flagged)}\n"
                    f"You MUST rewrite the response to immediately resolve these specific issues while maintaining the luxurious tone."
                )
        except Exception:
            # Fallback if Pydantic fails (should be rare)
            system_prompt += "\n\n### CRITICAL: Previous response rejected. Improve quality immediately."
    else:
        # Fallback to legacy string feedback if Packet not present but feedback is
        review_feedback = state.get("review_feedback")
        if review_feedback:
            system_prompt += (
                f"\n\n### CRITICAL INSTRUCTION (Correction Mode):\n"
                f"Your previous answer was rejected by the Academic Critic.\n"
                f"REWRITE IT based on this feedback:\n'{review_feedback}'\n"
                f"Ensure you address every point and maintain the luxurious tone."
            )

    # MAF-1.0 Integration: Audit Bundle Formatting
    maf_verification = state.get("maf_verification")
    if maf_verification and maf_verification.get("passed", False):
        system_prompt += (
            "\n\n### MAF-1.0 PROTOCOL: SEALED AUDIT BUNDLE\n"
            "You are creating the Final Audit Bundle. Your output MUST be structured as a formal Engineering Spec.\n"
            "1. **Claims**: List the key assertions.\n"
            "2. **Evidence**: Cite the proofs/reasoning used.\n"
            "3. **Verification**: Confirm the status (PASS).\n"
            "4. **Conclusion**: The final answer.\n"
            "Tone: Ultra-Professional, High-End Engineering, Authoritative."
        )

    # 5. Payload Construction
    final_user_content = f"Context:\n{context_text}\n\nStudent Question: {last_user_msg}"

    # 6. Execution
    final_text = await ai_client.send_message(
        system_prompt=system_prompt, user_message=final_user_content
    )

    return {
        "messages": [AIMessage(content=final_text)],
        "current_step_index": state.get("current_step_index", 0) + 1,
        "final_response": final_text,
    }
