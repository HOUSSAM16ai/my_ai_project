"""
المبادئ الصارمة للنظام على مستوى المشروع.

هذا الملف يمثل مصدر الحقيقة لمبادئ النظام الإلزامية
ويتيح الوصول البرمجي إليها بشكل موحد.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SystemPrinciple:
    """تمثيل مبدأ واحد من مبادئ النظام الصارمة."""

    number: int
    statement: str


SYSTEM_PRINCIPLES: tuple[SystemPrinciple, ...] = (
    SystemPrinciple(
        1,
        "تعدد الأشكال في البرمجة كائنية التوجه يسمح بواجهة واحدة لاستدعاء عمليات متعددة حسب نوع الكائن وقت التنفيذ.",
    ),
    SystemPrinciple(2, "لا يمكن إنشاء كائن (Instance) مباشرةً من فئة مجردة (Abstract Class)."),
    SystemPrinciple(
        3,
        "الوراثة تتيح إعادة استخدام الشيفرة عبر إنشاء فئة جديدة تعتمد على خصائص وسلوك فئة موجودة.",
    ),
    SystemPrinciple(
        4,
        "التغليف (Encapsulation) يعني إخفاء التفاصيل الداخلية للكائن وإظهار واجهة محددة للتعامل معه.",
    ),
    SystemPrinciple(
        5, "الدالة النقية لا تقوم بتعديل متغيرات عامة أو إحداث تأثيرات جانبية على حالة خارجية."
    ),
    SystemPrinciple(
        6,
        "الدالة عالية الرتبة (Higher-Order Function) هي دالة تأخذ دوالًا كوسائط أو تُرجع دالة كنتيجة.",
    ),
    SystemPrinciple(
        7, "التقييم الكسول (Lazy Evaluation) يعني تأجيل حساب التعبير حتى الحاجة الفعلية لقيمته."
    ),
    SystemPrinciple(
        8,
        "عدم قابلية التغيير (Immutability) يساعد على تجنب الاعتماد على حالة متغيرة أثناء التنفيذ كما في البرمجة الوظيفية.",
    ),
    SystemPrinciple(
        9,
        "الكومة الثنائية (Binary Heap) مناسبة لتنفيذ صف ذي أولوية (Priority Queue) للحصول على أعلى أولوية بكفاءة.",
    ),
    SystemPrinciple(
        10,
        "بنية Trie (Prefix Tree) تخزن الكلمات حسب البادئات وتتيح البحث بكفاءة اعتمادًا على البادئة.",
    ),
    SystemPrinciple(11, "البحث بعرض (BFS) يستخدم صفًّا (Queue) لزيارة العقد مستوىً بمستوى."),
    SystemPrinciple(
        12,
        "جدول التجزئة (Hash Table) يخزن أزواج المفتاح/القيمة ويتيح بحثًا بمتوسط زمن قريب من ‎O(1)‎.",
    ),
    SystemPrinciple(
        13, "شجرة AVL هي شجرة بحث ثنائية ذاتية الاتزان تضمن عمليات ‎O(log n)‎ في أسوأ الأحوال."
    ),
    SystemPrinciple(
        14,
        "البرمجة الديناميكية (Dynamic Programming) تحل المشكلة عبر مشاكل فرعية وتخزن النتائج لتجنب إعادة الحساب.",
    ),
    SystemPrinciple(
        15,
        "خوارزمية Backtracking تبني الحل تدريجيًا وتتراجع عند اكتشاف أن المسار الحالي لن يؤدي إلى حل صحيح.",
    ),
    SystemPrinciple(16, "تعقيد البحث الثنائي (Binary Search) في قائمة مرتبة هو ‎O(log n)‎."),
    SystemPrinciple(
        17,
        "الخوارزميات الجشعة (Greedy) تتخذ قرارًا محليًا أفضل في كل خطوة على أمل الوصول لحل عالمي جيد.",
    ),
    SystemPrinciple(
        18,
        "حالة السباق (Race Condition) تحدث عندما تتنافس خيوط متعددة على مورد مشترك فتنتج نتائج غير متوقعة.",
    ),
    SystemPrinciple(
        19,
        "خيوط العملية الواحدة تشترك في نفس مساحة الذاكرة، بينما العمليات المنفصلة تملك ذاكرة معزولة.",
    ),
    SystemPrinciple(
        20,
        "القفل (Mutex) يمنع دخول أكثر من خيط إلى القسم الحرج في الوقت نفسه ويساعد على منع السباقات.",
    ),
    SystemPrinciple(21, "Singleton مثال على نمط تصميم من أنماط عصابة الأربعة (GoF)."),
    SystemPrinciple(22, "نمط Observer يقوم فيه الـSubject بإخطار الـObservers عند تغيّر حالته."),
    SystemPrinciple(
        23, "مبادئ SOLID الخمسة تهدف لتحسين قابلية الفهم والتطوير والصيانة في التصميم الكائني."
    ),
    SystemPrinciple(
        24,
        "نظرية CAP تشير إلى: الاتساق (Consistency) والتوافرية (Availability) وتحمل التقسيم (Partition Tolerance).",
    ),
    SystemPrinciple(25, "RPC يسمح باستدعاء إجراء على خادم بعيد كما لو كان استدعاءً محليًا."),
    SystemPrinciple(
        26,
        "طوابير الرسائل تفصل المكونات عبر تواصل غير متزامن وتمكّن اختلاف سرعات المنتج والمستهلك دون فقد البيانات.",
    ),
    SystemPrinciple(27, "Git نظام تحكم إصدارات موزع لتتبع وإدارة تاريخ الشيفرة المصدرية."),
    SystemPrinciple(
        28, "Docker يوفّر حاويات لتشغيل التطبيق مع تبعياته في بيئة معزولة تشارك نواة النظام المضيف."
    ),
    SystemPrinciple(29, "CI/CD تعني التكامل المستمر والتسليم المستمر (وأحيانًا النشر المستمر)."),
    SystemPrinciple(
        30, "Haskell تُعد لغة وظيفية خالصة (Purely Functional) بشكل افتراضي مع تقييم كسول."
    ),
    SystemPrinciple(
        31,
        "جعل Square يرث من Rectangle مع تغيير سلوك setWidth/setHeight يخرق مبدأ استبدال ليسكوف (LSP) لأنه يمنع الاستبدال الآمن.",
    ),
    SystemPrinciple(
        32, "مبدأ Open/Closed ينص على أن الكيانات البرمجية مفتوحة للإضافة ومغلقة للتعديل."
    ),
    SystemPrinciple(33, "Java لا تدعم الوراثة المتعددة للفئات مباشرةً لتجنب غموض مشكلة الماس."),
    SystemPrinciple(
        34,
        "مبدأ Dependency Inversion يفرض أن تعتمد الوحدات على التجريدات لا على التفاصيل، وأن تعتمد التفاصيل أيضًا على التجريدات.",
    ),
    SystemPrinciple(
        35,
        "الدالة عديمة الآثار الجانبية لا تغيّر حالة خارجية (مثل متغير عام أو ملف أو طباعة)، وهذا يجعلها أسهل للاختبار والتوازي والتنبؤ.",
    ),
    SystemPrinciple(
        36,
        "التقييم الكسول في Haskell يسمح بتعريف بنى بيانات لانهائية لأن القيم لا تُحسب إلا عند الحاجة.",
    ),
    SystemPrinciple(37, "العودية (Recursion) تُستخدم كثيرًا بدل الحلقات في البرمجة الوظيفية."),
    SystemPrinciple(
        38, "عقدة B-Tree قد تحتوي عدة مفاتيح وعدة أبناء، ما يقلل ارتفاع الشجرة مقارنةً بـBST."
    ),
    SystemPrinciple(39, "Trie هي الأنسب للبحث بحسب بادئة نصية كما في الإكمال التلقائي."),
    SystemPrinciple(40, "خوارزمية Dijkstra لا تعمل بشكل صحيح بوجود أوزان سالبة."),
    SystemPrinciple(
        41,
        "معالجة تصادمات Hash يمكن أن تتم عبر Chaining (قائمة/بنية لكل خانة) أو Open Addressing (البحث عن خانة بديلة وفق نمط).",
    ),
    SystemPrinciple(
        42,
        "البرمجة الديناميكية تتطلب Optimal Substructure وتداخل المشاكل الفرعية (Overlapping Subproblems).",
    ),
    SystemPrinciple(
        43,
        "الخوارزمية التقريبية لمسألة NP-صعبة قد لا تعطي الحل الأمثل لكنها تضمن حدًا/نسبة تقريب بالنسبة للأمثل.",
    ),
    SystemPrinciple(44, "الشيفرة ذات الحلقة المثلثية (j من 1 إلى i) تعقيدها الكلي من رتبة ‎O(n^2)‎."),
    SystemPrinciple(
        45,
        "QuickSort متوسطه ‎O(n log n)‎ وقد يصبح ‎O(n^2)‎ في أسوأ الحالات عند اختيار Pivot سيئ باستمرار.",
    ),
    SystemPrinciple(
        46,
        "Deadlock يحدث عندما تنتظر خيوط متعددة موارد يحتجزها بعضها البعض بشكل دائري فلا يتقدم أي خيط.",
    ),
    SystemPrinciple(47, "نموذج Actor يعتمد على تمرير الرسائل دون مشاركة حالة مباشرة بين المكونات."),
    SystemPrinciple(
        48,
        "مثال Race Condition: خيطان يزيدان counter في نفس الوقت فيضيع أحد التحديثين، ويُمنع ذلك بقفل Mutex أو عمليات ذرّية (Atomic).",
    ),
    SystemPrinciple(
        49,
        "Concurrency تعني تداخل المهام منطقيًا، وParallelism تعني تنفيذها فعليًا في نفس اللحظة على أكثر من نواة/معالج.",
    ),
    SystemPrinciple(
        50, "نمط Strategy يتيح تبديل خوارزميات قابلة للتبادل أثناء التشغيل دون تغيير الكود العميل."
    ),
    SystemPrinciple(
        51,
        "Reactive Programming تعتمد على تدفقات بيانات غير متزامنة تنشر التغيّرات تلقائيًا للمشتركين.",
    ),
    SystemPrinciple(52, "MVC يفصل Model عن View وعن Controller لتحسين التنظيم والصيانة."),
    SystemPrinciple(
        53, "Eventual Consistency تعني أن العقد ستتوافق في النهاية إذا توقفت التحديثات الجديدة."
    ),
    SystemPrinciple(
        54, "2PC يضمن ذرّية المعاملة الموزعة بحيث تُعتمد لدى الجميع أو تُلغى لدى الجميع وفق قرار منسّق."
    ),
    SystemPrinciple(
        55,
        "Strong Consistency تضمن رؤية أحدث كتابة فورًا، بينما Eventual Consistency قد تُظهر قراءات قديمة مؤقتًا ثم تتقارب لاحقًا.",
    ),
    SystemPrinciple(
        56,
        "زمن الشبكة (Latency) قد يؤثر بشدة على أداء وصحة الأنظمة الموزعة ويجب تصميم النظام مع افتراض وجود تأخير.",
    ),
    SystemPrinciple(
        57,
        "VM تشغّل نظام تشغيل كاملًا لكل آلة افتراضية، بينما Container يشغّل التطبيق وتبعياته مع مشاركة نواة المضيف وبكلفة أخف.",
    ),
    SystemPrinciple(
        58, "Kubernetes منصة شائعة لأتمتة نشر وإدارة حاويات Docker مع التوسع والتعافي الذاتي."
    ),
    SystemPrinciple(
        59,
        "CI يدمج ويختبر باستمرار، وCD يجهّز النشر باستمرار (أو ينشر تلقائيًا في حالة Continuous Deployment).",
    ),
    SystemPrinciple(
        60,
        "Profiling يقيس استهلاك الموارد لتحديد اختناقات الأداء مثل دوال تستهلك أكثر وقت CPU أو ذاكرة.",
    ),
    SystemPrinciple(
        61,
        "Design by Contract يحدد شروطًا مسبقة ولاحقة وثوابت صنف لضمان صحة السلوك ورفع موثوقية البرمجية.",
    ),
    SystemPrinciple(
        62,
        "مشكلة الماس في الوراثة المتعددة تنشأ عندما تتقاطع وراثتان من أصل مشترك فتظهر إشكالية أي نسخة من الأساس تُستخدم.",
    ),
    SystemPrinciple(
        63,
        "الشيفرة C++ ستطبع “Derived” لأن foo افتراضية وسيتم الربط ديناميكيًا حسب النوع الفعلي للكائن.",
    ),
    SystemPrinciple(
        64,
        "مبدأ Interface Segregation ينص على ألا يُجبر العملاء على الاعتماد على واجهات لا يحتاجونها.",
    ),
    SystemPrinciple(
        65,
        "مبدأ المسؤولية الواحدة (SRP) يعني أن لكل صنف سببًا واحدًا للتغيير مما يقلل التعقيد ويزيد قابلية الصيانة.",
    ),
    SystemPrinciple(
        66,
        "الموناد (Monad) هي بنية تربط عمليات في سياق (مثل Maybe أو IO) عبر bind/return لتسلسل العمليات دون معالجة السياق يدويًا كل مرة.",
    ),
    SystemPrinciple(
        67,
        "Eager Evaluation يحسب القيم فورًا وهو أسهل للتنبؤ بالأداء، بينما Lazy Evaluation يؤجل الحساب وقد يوفر عملًا لكنه قد يصعّب توقع الذاكرة والزمن.",
    ),
    SystemPrinciple(
        68,
        "الدوال النقية والبيانات غير القابلة للتغيير تسهّل التوازي لأن غياب الآثار الجانبية يقلل الحاجة للتزامن.",
    ),
    SystemPrinciple(
        69,
        "Tail Recursion Optimization يحول الاستدعاء الذاتي الأخير إلى شكل حلقي لتقليل استهلاك المكدس ومنع Stack Overflow.",
    ),
    SystemPrinciple(
        70,
        "التعبير take 5 (iterate (+1) 0) ينتج [0,1,2,3,4] لأن iterate تولد قائمة لانهائية وtake يأخذ أول خمسة عناصر فقط.",
    ),
    SystemPrinciple(
        71,
        "Trie مناسبة للإكمال التلقائي لأنها تجعل زمن البحث مرتبطًا بطول البادئة وتسمح باستعراض كل الكلمات تحت عقدة البادئة.",
    ),
    SystemPrinciple(
        72,
        "Hash Table متوسطه ‎O(1)‎ لكن أسوأه قد يصل ‎O(n)‎، بينما الشجرة المتوازنة تضمن ‎O(log n)‎ في أسوأ الحالات.",
    ),
    SystemPrinciple(
        73, "Trie قد تستهلك ذاكرة أكبر عندما تكون مجموعة الكلمات كبيرة والتشارك في البادئات قليل."
    ),
    SystemPrinciple(
        74,
        "B-Tree ذات تفرع عالٍ تقلل عمق الشجرة وعدد عمليات I/O على القرص لذا تناسب قواعد البيانات والتخزين الخارجي.",
    ),
    SystemPrinciple(
        75,
        "أفضل نهج لاستخراج أكبر 10 قيم من مليون عنصر هو الاحتفاظ بـMin-Heap بحجم 10 أثناء المرور لتحقيق ‎O(n log 10)‎.",
    ),
    SystemPrinciple(
        76,
        "NP-Complete تعني أن المسألة في NP وكل مسائل NP يمكن اختزالها إليها، ولا يُعرف حل متعدد الحدود لها عمومًا.",
    ),
    SystemPrinciple(
        77,
        "Memoization أسلوب Top-Down مع كاش لنتائج الاستدعاءات العودية، وTabulation أسلوب Bottom-Up يبني جدولًا من الحالات الأصغر للأكبر.",
    ),
    SystemPrinciple(78, "إذا تضاعف n وزاد الزمن إلى 8× فالتعقيد المرجح هو ‎O(n^3)‎."),
    SystemPrinciple(
        79,
        "مثال خوارزمية تقريبية: Vertex Cover بخوارزمية تقريب 2-Approx التي تختار طرفي ضلع غير مغطى وتكرر حتى تغطية كل الأضلاع.",
    ),
    SystemPrinciple(
        80, "Bellman-Ford تصلح لإيجاد أقصر مسارات مع أوزان سالبة طالما لا توجد دورات سالبة."
    ),
    SystemPrinciple(
        81,
        "Semaphore يدير عددًا من “التصاريح” لمورد محدود، بينما Mutex قفل حصري لمورد واحد عادةً؛ مثلًا Semaphore بقيمة 3 يحد عدد الاتصالات المتزامنة إلى 3.",
    ),
    SystemPrinciple(
        82,
        "Data Parallelism يعني نفس العملية على أجزاء بيانات مختلفة (مثل جمع أجزاء مصفوفة)، وTask Parallelism يعني مهام مختلفة بالتوازي (مثل معالجة لون الصورة وتطبيق فلتر في آن واحد).",
    ),
    SystemPrinciple(
        83, "قانون أمدال يحدد حدًا أعلى للتسريع بسبب الجزء المتسلسل الذي لا يمكن موازنته بالكامل."
    ),
    SystemPrinciple(
        84,
        "GIL في CPython يمنع تنفيذ بايت كود بايثون في أكثر من خيط في نفس الوقت داخل نفس العملية، ما يحد من توازي المهام الحسابية.",
    ),
    SystemPrinciple(
        85,
        "Go تستخدم goroutines خفيفة وChannels للتواصل بأسلوب مستوحى من CSP عبر تمرير الرسائل بدل مشاركة الذاكرة.",
    ),
    SystemPrinciple(
        86,
        "Clean Architecture تعزل منطق الأعمال في الداخل وتفرض قاعدة الاعتماد بأن تتجه الاعتماديات نحو الداخل فقط لا نحو التفاصيل الخارجية.",
    ),
    SystemPrinciple(
        87,
        "Backpressure آلية لضبط تدفق البيانات عندما يكون المستهلك أبطأ من المنتج لتجنب الانهيار أو نفاد الذاكرة.",
    ),
    SystemPrinciple(
        88,
        "Dependency Injection يحقق DIP عمليًا بتمرير التبعيات من الخارج بدل إنشائها داخليًا، مما يقلل الاقتران ويسهّل الاختبار.",
    ),
    SystemPrinciple(
        89,
        "نمط Visitor يسمح بإضافة عمليات جديدة على كائنات متعددة دون تعديل تعريف هذه الكائنات عبر “زائر” ينفذ العمليات عليها.",
    ),
    SystemPrinciple(
        90,
        "Loose Coupling يعني اعتمادًا ضعيفًا بين المكونات عبر واجهات وتجريدات بحيث يمكن تغيير جزء دون كسر بقية النظام.",
    ),
    SystemPrinciple(
        91,
        "ACID يركز على الذرية والاتساق والعزل والدوام، بينما BASE يركز على التوافر الأساسي والحالة المرنة والاتساق النهائي في بعض NoSQL.",
    ),
    SystemPrinciple(
        92,
        "2PC يعمل بمرحلة Prepare للتصويت ثم مرحلة Commit/Abort لضمان أن الجميع يلتزم أو الجميع يتراجع.",
    ),
    SystemPrinciple(
        93,
        "نظام مصرفي غالبًا يفضل CP (اتساق + تحمل تقسيم) حتى لو ضحّى بالتوافرية أثناء الانقسام لتجنب أخطاء مالية.",
    ),
    SystemPrinciple(
        94,
        "Message Queue تفصل الخدمات وتزيد المرونة والتوسع عبر تخزين الرسائل ومعالجتها لاحقًا وتمكين زيادة عدد المستهلكين عند الذروة.",
    ),
    SystemPrinciple(
        95,
        "Idempotence مهمة لأنها تسمح بإعادة إرسال الطلبات أو تكرار التنفيذ عند الفشل دون مضاعفة الأثر النهائي.",
    ),
    SystemPrinciple(
        96,
        "git merge يدمج التاريخ مع Merge Commit ويحافظ على التشعب، بينما git rebase يعيد كتابة التاريخ ليصبح خطيًا ويُفضّل على الفروع الخاصة قبل مشاركتها.",
    ),
    SystemPrinciple(
        97,
        "Kubernetes يوفّر Self-healing بإعادة تشغيل الحاويات أو إعادة جدولة Pods عند الفشل للحفاظ على توفر الخدمة.",
    ),
    SystemPrinciple(
        98,
        "Blue-Green Deployment يستخدم بيئتين متطابقتين ويحوّل المرور من القديمة للجديدة دفعة واحدة لتقليل التوقف وتسهيل الرجوع السريع.",
    ),
    SystemPrinciple(
        99,
        "Distributed Tracing يربط الطلب عبر الخدمات باستخدام Trace ID وSpans ليُظهر أين حدث التأخير أو الخطأ داخل سلسلة الخدمات.",
    ),
    SystemPrinciple(
        100,
        "Logging وMonitoring وDistributed Tracing تشكل معًا أعمدة Observability لفهم الحالة الداخلية للنظام وتشخيص الأعطال بسرعة.",
    ),
)


def get_system_principles() -> tuple[SystemPrinciple, ...]:
    """الحصول على جميع مبادئ النظام الصارمة بشكل ثابت."""

    return SYSTEM_PRINCIPLES


def format_system_principles(
    *,
    header: str = "المبادئ الصارمة للنظام",
    bullet: str = "-",
    include_header: bool = True,
) -> str:
    """
    تنسيق مبادئ النظام الصارمة كنص جاهز للإدراج في السياقات المختلفة.

    Args:
        header: عنوان القسم.
        bullet: رمز التعداد النقطي.
        include_header: تحديد تضمين العنوان من عدمه.

    Returns:
        str: نص منسق للمبادئ.
    """
    prefix = f"{bullet} " if bullet else ""
    lines = [
        f"{prefix}{principle.number}. {principle.statement}" for principle in SYSTEM_PRINCIPLES
    ]
    body = "\n".join(lines)
    if include_header:
        return f"{header}\n{body}"
    return body


def validate_system_principles(
    principles: tuple[SystemPrinciple, ...] | None = None,
) -> None:
    """
    التحقق من سلامة مبادئ النظام الصارمة.

    يضمن هذا التحقق تطبيق المبادئ فعلياً عبر التأكد من:
    - اكتمال القائمة (100 مبدأ).
    - الترتيب والترقيم الصحيح (1..100 بدون تكرار).
    - وجود نص غير فارغ لكل مبدأ.

    Args:
        principles: قائمة المبادئ المطلوب التحقق منها. افتراضياً تستخدم القائمة الرسمية.

    Raises:
        ValueError: عند اكتشاف خلل في القائمة.
    """
    items = principles or SYSTEM_PRINCIPLES
    errors: list[str] = []
    expected_numbers = set(range(1, 101))
    numbers = [item.number for item in items]
    statements = [item.statement for item in items]

    if len(items) != 100:
        errors.append("عدد مبادئ النظام يجب أن يكون 100 مبدأ بالضبط.")

    if set(numbers) != expected_numbers:
        errors.append("ترقيم مبادئ النظام يجب أن يغطي النطاق الكامل من 1 إلى 100 دون تكرار.")

    if any(not statement.strip() for statement in statements):
        errors.append("يجب أن يحتوي كل مبدأ على نص غير فارغ.")

    if errors:
        message = "؛ ".join(errors)
        raise ValueError(message)
