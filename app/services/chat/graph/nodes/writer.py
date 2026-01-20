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
    # ERROR FIX: Previous regex was too broad and triggered on "don't give me solution".
    # New logic requires an explicit request verb OR a direct question.

    request_indicators = r"(أريد|بدي|ابغى|عطيني|اعطني|هات|وريني|show|give|want|provide|display|please|plz|من فضلك|لو سمحت)"
    target_nouns = r"(حل|إجابة|اجابة|جواب|صحح|تصحيح|solution|answer|result|correction)"

    # Match if:
    # 1. Indicator + Noun (ANY order) -> "Show solution", "Solution please"
    # 2. Noun + Question Mark -> "Solution?"
    # 3. Exact Noun only -> "Solution"

    # We construct a regex that looks for presence of Noun AND (Indicator OR QuestionMark OR Start/End anchor)

    last_msg_lower = last_user_msg.lower()
    has_noun = bool(re.search(target_nouns, last_msg_lower))
    is_request = bool(re.search(request_indicators, last_msg_lower))
    is_question = "?" in last_msg_lower or "؟" in last_msg_lower
    # Check for short phrase (e.g. "Solution", "الحل") - count tokens
    is_short = len(last_msg_lower.split()) <= 3

    # Negation check: e.g. "I don't want solution", "لا تعطيني الحل"
    # Matches "not" followed eventually by "want/give" or "solution"
    # Simple proximity check: "don't" ... "want/give"
    negation_pattern = r"(don't|do not|not|no|never|لا|ما|لم|لن|ليس).{0,20}(want|need|give|show|أريد|بدي|تعطيني|عطيني|هات)"
    has_negation = bool(re.search(negation_pattern, last_msg_lower))

    user_wants_solution = False
    if has_noun and not has_negation:
        if is_request or is_question:
            user_wants_solution = True
        elif is_short:
             # "The Solution", "الحل"
            user_wants_solution = True

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
