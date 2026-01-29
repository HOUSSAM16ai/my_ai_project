"""
Writer Node ("The Luxurious Simplification").
--------------------------------------------
Orchestrates the final response generation using a Strategy Pattern
to handle Student Intent, Context Firewalling, and Adaptive Prompting.
"""

from langchain_core.messages import AIMessage

from app.core.ai_gateway import AIClient
from app.core.di import Container
from app.core.interfaces import IContextComposer, IIntentDetector, IPromptStrategist
from app.services.chat.graph.components.context_composer import FirewallContextComposer
from app.services.chat.graph.components.intent_detector import RegexIntentDetector
from app.services.chat.graph.components.prompt_strategist import StandardPromptStrategist
from app.services.chat.graph.domain import StudentProfile
from app.services.chat.graph.state import AgentState

# Bootstrap Dependencies (This typically belongs in a bootstrap.py, placed here for self-containment in this refactor)
Container.register_singleton(IIntentDetector, RegexIntentDetector())
Container.register_singleton(IContextComposer, FirewallContextComposer())
Container.register_singleton(IPromptStrategist, StandardPromptStrategist())

# --- Main Node Orchestrator ---

async def writer_node(state: AgentState, ai_client: AIClient) -> dict:
    """
    The Orchestrator Function.
    Flow: Input -> Detect Intent -> Compose Context -> Build Prompt -> Generate.
    Refactored to use Dependency Injection (SOLID).
    """
    # 0. Resolve Dependencies
    intent_detector = Container.resolve(IIntentDetector)
    context_composer = Container.resolve(IContextComposer)
    prompt_strategist = Container.resolve(IPromptStrategist)

    # 1. Extraction
    messages = state["messages"]
    last_user_msg = messages[-1].content
    search_results = state.get("search_results", [])
    student_level = state.get("diagnosis", "Average")

    # 2. Analysis
    intent = intent_detector.analyze(last_user_msg)
    profile = StudentProfile(level=student_level)

    # 3. Composition
    context_text = context_composer.compose(search_results, intent)
    system_prompt = prompt_strategist.build_prompt(profile, intent)

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
