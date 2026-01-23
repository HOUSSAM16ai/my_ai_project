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
    تطبق 'Context Firewall' لمنع تسريب الحلول،
    ولكن إذا طلب المستخدم الحل، تقدمه بأسلوب مزدوج:
    1. الإجابة النموذجية الرسمية (للالتزام بسلم التنقيط).
    2. الشرح المخصص (Personalized Explanation) حسب مستوى الطالب.
    """
    messages = state["messages"]
    last_user_msg = messages[-1].content
    search_results = state.get("search_results", [])

    # Simulate diagnosis (In a real system, this comes from a Profile Service)
    # For now, we infer broadly or default to 'Average'.
    # We can inject this into the prompt.
    student_level = state.get("diagnosis", "Average")

    # --- Genius Context Firewall ---
    request_indicators = r"(أريد|بدي|ابغى|عطيني|اعطني|هات|وريني|show|give|want|provide|display|please|plz|من فضلك|لو سمحت)"
    target_nouns = r"(حل|إجابة|اجابة|جواب|صحح|تصحيح|solution|answer|result|correction)"

    last_msg_lower = last_user_msg.lower()
    has_noun = bool(re.search(target_nouns, last_msg_lower))
    is_request = bool(re.search(request_indicators, last_msg_lower))
    is_question = "?" in last_msg_lower or "؟" in last_msg_lower
    is_short = len(last_msg_lower.split()) <= 3
    negation_pattern = r"(don't|do not|not|no|never|لا|ما|لم|لن|ليس).{0,20}(want|need|give|show|أريد|بدي|تعطيني|عطيني|هات)"
    has_negation = bool(re.search(negation_pattern, last_msg_lower))

    user_wants_solution = False
    if has_noun and not has_negation:
        if is_request or is_question:
            user_wants_solution = True
        elif is_short:
            user_wants_solution = True

    # Prepare Context with Firewall
    context_text = ""
    if search_results:
        for item in search_results:
            content = item.get("content", "")
            original_solution = item.get("solution", "")

            if user_wants_solution:
                # If user wants solution, we provide the FULL Official Solution Key
                solution_text = original_solution
                solution_display = f"### الحل النموذجي (Official Solution):\n{solution_text}"
            else:
                solution_display = "[SOLUTION HIDDEN: Student has NOT requested the solution yet.]"

            context_text += f"Exercise:\n{content}\n\n{solution_display}\n\n---\n"

    system_prompt = (
        "أنت 'Overmind'، المعلم الذكي (Smart Tutor) والموجه الأكاديمي الفاخر.\n"
        "مهمتك: مساعدة الطالب باستخدام المحتوى المسترجع (Context) بذكاء وحكمة.\n\n"

        "القواعد الصارمة (The Golden Rules):\n"
        "1. **تحليل طلب الطالب بدقة**: إذا طلب 'تمرين' فقط، قدم نص التمرين **فقط**.\n"
        "2. **سرية الحلول**: لاحظ أن السياق قد يخفي الحل (SOLUTION HIDDEN). هذا مقصود.\n"

        "3. **عند طلب الحل (Dual Mode Protocol)**:\n"
        "   - **الجزء الأول (الصرامة):** يجب أن تعرض 'الحل النموذجي الرسمي' (Official Answer Key) وسلم التنقيط كما هو بالضبط.\n"
        "     ⚠️ **هام جداً:** اعرض الحل الرسمي تحت عنوان واضح (مثلاً: ### الحل النموذجي) لضمان التنسيق الجيد.\n"
        "   - **الجزء الثاني (المرونة):** بعد الحل، قدم 'شرحاً خارقاً مخصصاً' (Supernatural Personalized Explanation).\n"
        f"   - **تخصيص الشرح:** مستوى الطالب الحالي هو: **{student_level}**.\n"
        "     - إذا كان 'Beginner': اشرح الأساسيات بتبسيط شديد، فكك المصطلحات، واستخدم تشبيهات من الواقع.\n"
        "     - إذا كان 'Average': ركز على توضيح النقاط الصعبة والربط بين المفاهيم.\n"
        "     - إذا كان 'Advanced': قدم تحديات إضافية، ناقش طرق حل بديلة، وركز على السرعة والدقة.\n\n"

        "4. **تجنب الهلوسة**: إذا لم تجد المحتوى، اعتذر بلطف.\n"
        "5. حافظ على أسلوب تربوي ممتع، محفز، وفاخر جداً.\n"
    )

    # Using send_message which is compatible with NeuralRoutingMesh
    user_content = f"Context:\n{context_text}\n\nQuestion: {last_user_msg}"

    final_text = await ai_client.send_message(
        system_prompt=system_prompt,
        user_message=user_content
    )

    return {
        "messages": [AIMessage(content=final_text)],
        "current_step_index": state["current_step_index"] + 1,
        "final_response": final_text
    }
