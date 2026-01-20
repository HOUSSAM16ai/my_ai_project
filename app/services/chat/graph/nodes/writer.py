"""
عقدة الكاتب (Writer Node).
--------------------------
تقوم بصياغة الإجابة النهائية بأسلوب 'Smart Tutor'.
"""

from langchain_core.messages import AIMessage
from app.services.chat.graph.state import AgentState
from app.core.ai_gateway import AIClient
from app.core.ai_config import get_ai_config

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
            context_text += f"Exercise:\n{content}\n\n<HIDDEN_SOLUTION_DO_NOT_REVEAL>\n{solution}\n</HIDDEN_SOLUTION_DO_NOT_REVEAL>\n\n---\n"

    system_prompt = (
        "أنت 'Overmind'، المعلم الذكي (Smart Tutor) والموجه الأكاديمي.\n"
        "مهمتك: مساعدة الطالب باستخدام المحتوى المسترجع (Context) بذكاء وحكمة.\n"
        "القواعد الصارمة:\n"
        "1. **تحليل طلب الطالب بدقة**: إذا طلب 'تمرين' فقط، قدم نص التمرين **فقط** ولا تذكر الحل أو النتيجة النهائية أبداً.\n"
        "2. **سرية الحلول**: المحتوى الموجود داخل وسوم <HIDDEN_SOLUTION_DO_NOT_REVEAL> هو **حل سري**. يمنع منعاً باتاً كشفه أو تسريبه للطالب ما لم يطلب الطالب الحل صراحة (مثلاً: 'أعطني الحل'، 'اشرح لي').\n"
        "3. **الوضع الافتراضي**: إذا لم يحدد الطالب، قدم التمرين واترك له فرصة للمحاولة، أو قدم تلميحاً بسيطاً من فهمك للتمرين دون كشف الحل.\n"
        "4. **تجنب الهلوسة**: إذا لم تجد المحتوى، اعتذر بلطف. لا تختلق رسائل نظام رسمية مثل 'Overmind system announces...'. تحدث بشكل طبيعي كمعلم.\n"
        "5. حافظ على أسلوب تربوي ممتع، محفز، وفاخر.\n"
    )

    last_user_msg = messages[-1].content

    input_messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Context:\n{context_text}\n\nQuestion: {last_user_msg}"}
    ]

    response = await ai_client.generate(
        model=get_ai_config().primary_model,
        messages=input_messages
    )

    final_text = response.choices[0].message.content

    return {
        "messages": [AIMessage(content=final_text)],
        "current_step_index": state["current_step_index"] + 1,
        "final_response": final_text
    }
