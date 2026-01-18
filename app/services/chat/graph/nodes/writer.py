"""
عقدة الكاتب (Writer Node).
--------------------------
تقوم بصياغة الإجابة النهائية بأسلوب 'Smart Tutor'.
"""

from langchain_core.messages import AIMessage
from app.services.chat.graph.state import AgentState
from app.core.ai_gateway import AIClient

async def writer_node(state: AgentState, ai_client: AIClient) -> dict:
    """
    عقدة الكتابة: تصيغ الرد النهائي.
    """
    messages = state["messages"]
    search_results = state.get("search_results", [])

    # Prepare Context
    context_text = ""
    if search_results:
        for item in search_results:
            content = item.get("content", "")
            solution = item.get("solution", "")
            context_text += f"Exercise:\n{content}\n\nSolution:\n{solution}\n\n---\n"

    system_prompt = (
        "أنت 'Overmind'، المعلم الذكي (Smart Tutor).\n"
        "مهمتك: الإجابة على سؤال الطالب بناءً على المحتوى المسترجع.\n"
        "القواعد:\n"
        "1. استخدم المحتوى المسترجع (Context) بدقة.\n"
        "2. اشرح الحل بأسلوب تربوي ممتع وفاخر.\n"
        "3. إذا لم يوجد محتوى، أجب بناءً على معرفتك العامة لكن نبه الطالب.\n"
    )

    last_user_msg = messages[-1].content

    input_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {last_user_msg}"}
    ]

    response = await ai_client.generate(
        model="gpt-4o",
        messages=input_messages
    )

    final_text = response.choices[0].message.content

    return {
        "messages": [AIMessage(content=final_text)],
        "current_step_index": state["current_step_index"] + 1,
        "final_response": final_text
    }
