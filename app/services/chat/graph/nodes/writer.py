"""
عقدة الكاتب (Writer Node).
--------------------------
تقوم بصياغة الإجابة النهائية بأسلوب 'Smart Tutor'.
"""

import re
from langchain_core.messages import AIMessage
from app.services.chat.graph.state import AgentState
from app.core.ai_gateway import AIClient
from app.core.ai_config import get_ai_config

async def writer_node(state: AgentState, ai_client: AIClient) -> dict:
    """
    عقدة الكتابة: تصيغ الرد النهائي.
    تطبق 'Context Firewall' لمنع تسريب الحلول.
    """
    messages = state["messages"]
    last_user_msg = messages[-1].content
    search_results = state.get("search_results", [])

    # --- Genius Context Firewall ---
    # Determine if user *explicitly* requested the solution/answer.
    # We use regex for robustness against slight phrasing variations.
    solution_keywords = r"(حل|إجابة|اجابة|نتيجة|جواب|صحح|تصحيح|solution|answer|result|correct|solve)"

    # Check if the user message contains any of the solution keywords
    user_wants_solution = bool(re.search(solution_keywords, last_user_msg.lower()))

    # Prepare Context with Firewall
    context_text = ""
    if search_results:
        for item in search_results:
            content = item.get("content", "")
            original_solution = item.get("solution", "")

            # THE FIREWALL:
            # If user didn't ask for solution, we physically remove it from the text sent to the LLM.
            # This makes it impossible for the LLM to leak it.
            if user_wants_solution:
                solution_text = original_solution
                # Even if they want it, we wrap it to be safe/organized
                solution_display = f"<SOLUTION>\n{solution_text}\n</SOLUTION>"
            else:
                # Replacement text - LLM sees this instead of the real answer
                solution_display = "[SOLUTION HIDDEN: Student has NOT requested the solution yet.]"

            context_text += f"Exercise:\n{content}\n\n{solution_display}\n\n---\n"

    system_prompt = (
        "أنت 'Overmind'، المعلم الذكي (Smart Tutor) والموجه الأكاديمي.\n"
        "مهمتك: مساعدة الطالب باستخدام المحتوى المسترجع (Context) بذكاء وحكمة.\n"
        "القواعد الصارمة:\n"
        "1. **تحليل طلب الطالب بدقة**: إذا طلب 'تمرين' فقط، قدم نص التمرين **فقط**.\n"
        "2. **سرية الحلول**: لاحظ أن السياق قد يخفي الحل (SOLUTION HIDDEN). هذا مقصود. لا تحاول تخمين الحل إذا كان مخفياً.\n"
        "3. **تقديم الحل**: إذا كان الحل متاحاً (بين وسوم <SOLUTION>)، قدمه بأسلوب شرح تربوي خطوة بخطوة.\n"
        "4. **تجنب الهلوسة**: إذا لم تجد المحتوى، اعتذر بلطف. لا تختلق رسائل نظام رسمية مثل 'Overmind system announces...'.\n"
        "5. حافظ على أسلوب تربوي ممتع، محفز، وفاخر.\n"
    )

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
