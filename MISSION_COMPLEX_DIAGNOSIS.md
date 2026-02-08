# تشخيص شامل للمهمة الخارقة (Mission Complex Diagnosis)

## 1. نظرة عامة (Overview)
المهمة الخارقة "Mission Complex" هي نظام متقدم متعدد الوكلاء (Multi-Agent System) مبني على إطار العمل **LangGraph**، يهدف لحل المشكلات المعقدة عبر سلسلة من العمليات المعرفية المنظمة: التخطيط، التصميم، التنفيذ، والتدقيق. النظام ليس مجرد "Chatbot" بسيط، بل هو عقل رقمي متكامل (Overmind).

## 2. هيكلة النظام (System Architecture)

### 2.1 الواجهة الأمامية (Frontend)
- **المكون المسؤول:** `frontend/app/components/CogniForgeApp.jsx`
- **آلية العمل:**
  - يتم اختيار نوع المهمة عبر `MissionSelector` بقيمة `mission_complex`.
  - يتم إنشاء اتصال WebSocket وإرسال البيانات الوصفية: `{ mission_type: 'mission_complex' }`.
  - يعتمد النظام على استقبال الأحداث (Events) لعرض التقدم للمستخدم.

### 2.2 بوابة الدخول الخلفية (Backend Entry Point)
- **المعالج:** `MissionComplexHandler` في `app/services/chat/handlers/strategy_handlers.py`.
- **الدور:**
  - استقبال الطلب وتحديد النية `ChatIntent.MISSION_COMPLEX`.
  - إنشاء سجل `Mission` في قاعدة البيانات بحالة `PENDING`.
  - إطلاق المهمة في عملية خلفية (`_run_mission_bg`) لعدم تعطيل الاتصال.
  - الاشتراك في `EventBus` لبث التحديثات للمستخدم.

### 2.3 العقل المدبر (The Brain: LangGraphOvermindEngine)
- **الموقع:** `app/services/overmind/langgraph/engine.py`
- **التصميم:**
  - يستخدم نمط **Supervisor-Worker** لتوزيع المهام.
  - يتكون من عقد (Nodes) تمثل الوكلاء المتخصصين.
  - يحتفظ بحالة مشتركة (`LangGraphState`) تمر بين الوكلاء.

## 3. تحليل الوكلاء (Agents Analysis)

### 3.1 السياقي (Contextualizer)
- **المهمة:** إثراء طلب المستخدم بمعلومات خارجية قبل البدء.
- **نقطة الفشل الحرجة:** يعتمد على `ContextEnricher` الذي يستخدم `ResearchAgentClient`. إذا كان المتغير البيئي `RESEARCH_AGENT_URL` غير مضبوط أو الخدمة غير متاحة، يعود بـ `NullSnippetRetriever` مما يعني **سياق فارغ**.

### 3.2 الاستراتيجي (Strategist)
- **المهمة:** وضع خطة عمل (Plan) بناءً على الهدف والسياق.
- **نقطة الفشل الحرجة:**
  - يعتمد كلياً على `OPENROUTER_API_KEY`.
  - في حال غياب المفتاح، يعود بخطة طوارئ "AI Service Unavailable".
  - إذا كان السياق فارغاً (بسبب فشل السياقي)، قد يولد خطة عامة غير مفيدة (مثل "ابحث عن المعلومات" دون تفاصيل).

### 3.3 المنفذ (Operator)
- **المهمة:** تنفيذ خطوات الخطة باستخدام الأدوات المتاحة.
- **الأداة المستخدمة:** `TaskExecutor` (`app/services/overmind/executor.py`).
- **المشكلة الكبرى (Root Cause):**
  - يعتمد التنفيذ على الأدوات المسجلة في `ToolRegistry`.
  - الأداة الأساسية للبحث هي `search_educational_content` (`app/services/chat/tools/retrieval/service.py`).

## 4. التشخيص الدقيق للمشكلة (Root Cause Analysis)

### السبب الأول: التحقق الصارم من البيانات الوصفية (Strict Metadata Verification)
**الموقع:** `app/services/chat/tools/retrieval/service.py`
**الوصف:** تحتوي أداة البحث `search_educational_content` على منطق تحقق صارم جداً:
```python
if year and str(payload.get("year", "")) != str(year):
    continue
```
**الأثر:** إذا طلب المستخدم تمريناً لعام "2024" وكانت قاعدة البيانات تحتوي على "2023" أو كانت المعلومة ناقصة، يتم **تجاهل النتيجة تماماً**. هذا يؤدي إلى إرجاع "لا يوجد نتائج" حتى لو كان المحتوى موجوداً ولكنه غير مفهرس بدقة 100%.

### السبب الثاني: ازدواجية أدوات البحث (Tool Duplicity)
- يوجد أداتان للبحث:
  1. `search_educational_content`: (القديمة، صارمة جداً، غالباً ما تفشل).
  2. `search_content`: (الجديدة، تستخدم `SuperSearchOrchestrator`، أكثر مرونة).
- **المشكلة:** إذا قام "الاستراتيجي" باختيار الأداة القديمة (بناءً على وصفها في الـ Prompt)، سيفشل البحث. يجب توجيه النظام لاستخدام `search_content` حصراً.

### السبب الثالث: الاعتماد على الخدمات المصغرة (Dependency fragility)
- الكود في `app/services/chat/tools/content.py` يستورد مباشرة من `microservices.research_agent`.
- أي خطأ في إعدادات `PYTHONPATH` أو غياب ملفات الـ Microservice سيؤدي إلى فشل الأداة بصمت (أو بأخطاء يتم التقاطها وتسجيلها فقط).

### السبب الرابع: غياب التغذية الراجعة (Missing Feedback Loop)
- في حال فشل المهمة الخلفية (`_run_mission_bg`)، يلتقط الـ Handler الخطأ ويسجله (`logger.exception`), لكنه قد لا ينجح دائماً في إرسال رسالة خطأ واضحة للمستخدم عبر الـ WebSocket إذا كان الاتصال قد أغلق أو لم يبدأ البث بعد.

## 5. التوصيات والحلول (Recommendations)

1.  **إصلاح أداة البحث (Immediate Fix):** تعديل `app/services/chat/tools/retrieval/service.py` لتخفيف حدة التحقق (Fuzzy Matching) بدلاً من التطابق الحرفي الصارم، أو استبدال منطقها الداخلي ليستخدم `SuperSearchOrchestrator` مباشرة.
2.  **تحديث توجيه الأدوات:** التأكد من أن "الاستراتيجي" يفضل استخدام `search_content` بدلاً من `search_educational_content`.
3.  **التحقق من البيئة:** التأكد من وجود `RESEARCH_AGENT_URL` و `OPENROUTER_API_KEY` في بيئة التشغيل.
4.  **تحسين التعامل مع الأخطاء:** ضمان إرسال حدث `MISSION_ERROR` للمستخدم في حال فشل المعالجة الخلفية بوضوح.

---
**الحالة النهائية:** النظام مصمم بهيكلية ممتازة (Overmind/LangGraph) ولكنه يعاني من "هشاشة" في نقاط التكامل (Integration Points) وتشدد مبالغ فيه في فلترة نتائج البحث، مما يجعله يبدو وكأنه "لا يعمل".
