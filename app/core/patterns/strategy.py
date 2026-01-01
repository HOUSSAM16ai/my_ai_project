"""
نمط الاستراتيجية (Strategy Pattern) - تطبيق احترافي عالمي المستوى
====================================================================

يوفر هذا الموديول تطبيقاً عاماً وقوياً لنمط الاستراتيجية (Strategy Pattern)
لاختيار وتنفيذ خوارزميات مختلفة في وقت التشغيل (Runtime Algorithm Selection).

المبادئ المطبقة (Applied Principles):
--------------------------------------
✅ Harvard CS50 2025:
   - Type Safety: استخدام Generic[TInput, TOutput] للأمان الكامل
   - Async/Await: دعم كامل للعمليات غير المتزامنة
   - Error Handling: معالجة شاملة للأخطاء مع Logging
   - Clean Code: كود نظيف ومفهوم وسهل الصيانة

✅ Berkeley CS61 (SICP):
   - Higher-Order Functions: الاستراتيجيات كدوال من مستوى أعلى
   - Data Abstraction: فصل واضح بين الواجهة والتطبيق
   - Message Passing: الاستراتيجيات تتواصل عبر بروتوكول موحد
   - Dispatch on Type: اختيار الاستراتيجية بناءً على السياق

✅ Berkeley CS61 (Systems):
   - Concurrency: دعم كامل للعمليات المتزامنة (async/await)
   - Performance: تحسين الأداء مع Priority Ordering
   - Error Recovery: استمرار العمل عند فشل استراتيجية واحدة

✅ SOLID Principles:
   - Single Responsibility: كل استراتيجية مسؤولة عن خوارزمية واحدة
   - Open/Closed: مفتوح للتوسع (إضافة استراتيجيات جديدة) دون تعديل
   - Liskov Substitution: يمكن استبدال أي استراتيجية بأخرى
   - Interface Segregation: واجهة بسيطة ومحددة (can_handle + execute)
   - Dependency Inversion: الاعتماد على التجريد وليس التنفيذ

الاستخدام (Usage):
------------------
    from app.core.patterns.strategy import Strategy, StrategyRegistry

    # 1. تعريف السياق (Context Definition)
    @dataclass
    class PaymentContext:
        amount: Decimal
        method: str  # "credit_card" | "paypal" | "crypto"
        currency: str = "USD"

    # 2. تطبيق الاستراتيجيات (Implement Strategies)
    class CreditCardStrategy(Strategy[PaymentContext, bool]):
        async def can_handle(self, context: PaymentContext) -> bool:
            '''يمكنه معالجة الدفع ببطاقة الائتمان'''
            return context.method == "credit_card"

        async def execute(self, context: PaymentContext) -> bool:
            '''تنفيذ الدفع ببطاقة الائتمان'''
            # معالجة الدفع...
            return True

        @property
        def priority(self) -> int:
            return 10  # أولوية عالية

    class PayPalStrategy(Strategy[PaymentContext, bool]):
        async def can_handle(self, context: PaymentContext) -> bool:
            '''يمكنه معالجة الدفع عبر PayPal'''
            return context.method == "paypal"

        async def execute(self, context: PaymentContext) -> bool:
            '''تنفيذ الدفع عبر PayPal'''
            # معالجة الدفع...
            return True

        @property
        def priority(self) -> int:
            return 5  # أولوية متوسطة

    # 3. تسجيل واستخدام (Register and Use)
    registry = StrategyRegistry[PaymentContext, bool]()
    registry.register(CreditCardStrategy())
    registry.register(PayPalStrategy())

    # 4. التنفيذ (Execution)
    context = PaymentContext(amount=Decimal("99.99"), method="credit_card")
    success = await registry.execute(context)

    if success:
        print("✅ الدفع نجح!")
    else:
        print("❌ الدفع فشل!")

مثال متقدم مع Async Generators:
---------------------------------
    class StreamingStrategy(Strategy[str, AsyncGenerator[str, None]]):
        async def can_handle(self, context: str) -> bool:
            return context.startswith("stream:")

        async def execute(self, context: str) -> AsyncGenerator[str, None]:
            '''بث النتائج بشكل تدريجي'''
            for i in range(5):
                await asyncio.sleep(0.1)
                yield f"Chunk {i}: {context}"

    # الاستخدام:
    registry = StrategyRegistry[str, AsyncGenerator[str, None]]()
    registry.register(StreamingStrategy())

    result = await registry.execute("stream:data")
    if result:
        async for chunk in result:
            print(chunk)

الفوائد (Benefits):
-------------------
✅ فصل الخوارزميات عن السياق (Algorithm-Context Separation)
✅ سهولة إضافة خوارزميات جديدة (Easy to add new algorithms)
✅ اختيار ديناميكي في وقت التشغيل (Dynamic runtime selection)
✅ دعم الأولويات لترتيب المحاولات (Priority-based ordering)
✅ معالجة أخطاء قوية مع Fallback (Robust error handling)
✅ دعم كامل للعمليات غير المتزامنة (Full async/await support)
✅ دعم Async Generators للبث التدريجي (Streaming support)

الأنماط المدعومة (Supported Patterns):
---------------------------------------
1. Synchronous Strategies (عمليات متزامنة)
2. Async/Await Strategies (عمليات غير متزامنة)
3. Async Generator Strategies (بث تدريجي)
4. Priority-Based Selection (اختيار حسب الأولوية)
5. Error Recovery (استمرار عند الفشل)

المراجع (References):
---------------------
- Gang of Four: Design Patterns (Strategy Pattern)
- Martin Fowler: Patterns of Enterprise Application Architecture
- Robert C. Martin: Clean Architecture
- SICP Chapter 2: Building Abstractions with Data
"""

import inspect
import logging
from abc import ABC, abstractmethod
from typing import Generic, TypeVar

# إعداد Logger للتتبع والتشخيص
logger = logging.getLogger(__name__)

# متغيرات النوع العام (Generic Type Variables)
TInput = TypeVar("TInput")   # نوع مدخلات الاستراتيجية
TOutput = TypeVar("TOutput")  # نوع مخرجات الاستراتيجية


class Strategy(ABC, Generic[TInput, TOutput]):
    """
    فئة أساسية مجردة للاستراتيجيات (Abstract Base Class for Strategies).

    الاستراتيجية تُغلّف خوارزمية وتوفر واجهة موحدة لتنفيذها
    بناءً على السياق المُعطى (Context-based Execution).

    المبدأ الأساسي (Core Principle):
        "تعريف عائلة من الخوارزميات، تغليف كل منها، وجعلها قابلة للتبديل.
        الاستراتيجية تسمح للخوارزمية بالتغير بشكل مستقل عن العملاء الذين يستخدمونها."
        - Gang of Four

    Generic Parameters:
        TInput: نوع مدخلات الاستراتيجية (Input context type)
        TOutput: نوع مخرجات الاستراتيجية (Output result type)

    Abstract Methods:
        - can_handle(context): هل يمكن للاستراتيجية معالجة هذا السياق؟
        - execute(context): تنفيذ الاستراتيجية على السياق المُعطى

    Optional Properties:
        - priority: أولوية الاستراتيجية (افتراضياً: 0)

    Example Implementation:
        class PremiumUserStrategy(Strategy[User, Discount]):
            '''استراتيجية للمستخدمين المميزين'''

            async def can_handle(self, context: User) -> bool:
                '''التحقق من أن المستخدم مميز'''
                return context.is_premium and context.subscription_active

            async def execute(self, context: User) -> Discount:
                '''منح خصم 20% للمستخدمين المميزين'''
                return Discount(
                    percentage=20,
                    reason="عميل مميز",
                    valid_until=context.subscription_end_date
                )

            @property
            def priority(self) -> int:
                '''أولوية عالية للمستخدمين المميزين'''
                return 100

        class RegularUserStrategy(Strategy[User, Discount]):
            '''استراتيجية للمستخدمين العاديين'''

            async def can_handle(self, context: User) -> bool:
                '''يمكنها معالجة أي مستخدم (fallback)'''
                return True

            async def execute(self, context: User) -> Discount:
                '''منح خصم 5% للمستخدمين العاديين'''
                return Discount(
                    percentage=5,
                    reason="خصم عام",
                    valid_until=None
                )

            @property
            def priority(self) -> int:
                '''أولوية منخفضة (استراتيجية احتياطية)'''
                return 0

    Design Decisions (CS61 Systems):
        ✅ Async-First: جميع الدوال async لدعم I/O غير المتزامن
        ✅ Priority Ordering: الاستراتيجيات ذات الأولوية العالية تُجرّب أولاً
        ✅ Fail-Safe: إذا فشلت استراتيجية، نحاول التالية
        ✅ Logging: تسجيل كامل للعمليات للتشخيص

    Complexity Analysis:
        - can_handle(): O(1) في معظم الحالات
        - execute(): يعتمد على تطبيق الاستراتيجية
        - priority: O(1) - خاصية بسيطة
    """

    @abstractmethod
    async def can_handle(self, context: TInput) -> bool:
        """
        تحديد ما إذا كانت هذه الاستراتيجية يمكنها معالجة السياق المُعطى.

        يجب على الفئات الفرعية تطبيق هذه الدالة للتحقق من:
        - هل البيانات المطلوبة متوفرة في السياق؟
        - هل الشروط الخاصة بهذه الاستراتيجية متحققة؟
        - هل الاستراتيجية مناسبة لهذا النوع من المدخلات؟

        ملاحظة مهمة:
            يجب أن تكون هذه الدالة سريعة (fast check) لأنها تُستدعى
            لكل استراتيجية مسجلة. تجنب العمليات الثقيلة هنا.

        Args:
            context: السياق المُعطى للتقييم (Input context to evaluate)

        Returns:
            bool: True إذا كانت الاستراتيجية يمكنها معالجة هذا السياق

        Example:
            async def can_handle(self, context: PaymentContext) -> bool:
                '''التحقق من توفر معلومات بطاقة الائتمان'''
                return (
                    context.payment_method == "credit_card" and
                    context.card_number is not None and
                    len(context.card_number) == 16
                )

        Complexity: يجب أن تكون O(1) أو O(log n) على الأكثر
        """
        pass

    @abstractmethod
    async def execute(self, context: TInput) -> TOutput:
        """
        تنفيذ خوارزمية الاستراتيجية على السياق المُعطى.

        يجب على الفئات الفرعية تطبيق هذه الدالة لتنفيذ
        المنطق الأساسي للاستراتيجية.

        القواعد المهمة:
        ✅ يجب التحقق من صحة المدخلات
        ✅ معالجة الأخطاء بشكل مناسب
        ✅ تسجيل العمليات المهمة (logging)
        ✅ إرجاع نتيجة واضحة ومحددة

        Args:
            context: السياق المُعطى للمعالجة (Input context to process)

        Returns:
            TOutput: نتيجة تنفيذ الاستراتيجية

        Raises:
            ValueError: إذا كانت البيانات غير صالحة
            RuntimeError: إذا حدث خطأ أثناء التنفيذ
            NotImplementedError: إذا لم يتم تطبيق الدالة

        Example (Coroutine):
            async def execute(self, context: User) -> Report:
                '''إنشاء تقرير للمستخدم'''
                # جمع البيانات
                orders = await self.db.get_user_orders(context.id)
                stats = self._calculate_stats(orders)
                
                # إنشاء التقرير
                return Report(
                    user_id=context.id,
                    total_orders=len(orders),
                    statistics=stats
                )

        Example (Async Generator):
            async def execute(self, context: str) -> AsyncGenerator[str, None]:
                '''بث النتائج تدريجياً'''
                results = await self.search(context)
                for result in results:
                    processed = await self.process(result)
                    yield processed

        Complexity: يعتمد على تطبيق الاستراتيجية
        """
        pass

    @property
    def priority(self) -> int:
        """
        الحصول على أولوية هذه الاستراتيجية.

        الاستراتيجيات ذات الأولوية الأعلى تُقيّم أولاً (Higher priority = evaluated first).
        هذا مفيد عندما يكون لديك استراتيجيات متعددة يمكنها معالجة نفس السياق.

        الأولويات النموذجية (Typical Priorities):
        - 100+: أولوية عالية جداً (حالات خاصة، مستخدمين VIP)
        - 50-99: أولوية عالية (مستخدمين مميزين)
        - 10-49: أولوية متوسطة (حالات عامة)
        - 1-9: أولوية منخفضة (حالات نادرة)
        - 0: أولوية افتراضية (استراتيجية احتياطية)
        - سالب: يُستخدم فقط كحل أخير

        Returns:
            int: قيمة الأولوية (الافتراضي: 0)

        Example:
            @property
            def priority(self) -> int:
                '''أولوية عالية للمعالجة السريعة'''
                return 80

        Complexity: O(1) - خاصية بسيطة
        """
        return 0


class StrategyRegistry(Generic[TInput, TOutput]):
    """
    سجل لإدارة وتنفيذ الاستراتيجيات (Registry for Managing and Executing Strategies).

    السجل يحتفظ بمجموعة من الاستراتيجيات ويختار الاستراتيجية
    المناسبة بناءً على سياق المدخلات (Input Context).

    المسؤوليات الأساسية (Core Responsibilities):
    1. تسجيل الاستراتيجيات (Register strategies)
    2. ترتيبها حسب الأولوية (Sort by priority)
    3. اختيار الاستراتيجية المناسبة (Select appropriate strategy)
    4. تنفيذ الاستراتيجية (Execute strategy)
    5. معالجة الأخطاء والاستمرار (Handle errors and continue)

    المبادئ المطبقة (Applied Principles):
        ✅ Single Responsibility: إدارة الاستراتيجيات فقط
        ✅ Open/Closed: إضافة استراتيجيات جديدة دون تعديل
        ✅ Error Recovery: المرونة في معالجة الأخطاء
        ✅ Priority-Based Dispatch: اختيار ذكي بناءً على الأولوية

    Generic Parameters:
        TInput: نوع مدخلات الاستراتيجيات
        TOutput: نوع مخرجات الاستراتيجيات

    Attributes:
        _strategies: قائمة الاستراتيجيات المسجلة (مرتبة حسب الأولوية)

    Example Usage:
        # 1. إنشاء السجل
        registry = StrategyRegistry[PaymentRequest, PaymentResult]()

        # 2. تسجيل الاستراتيجيات
        registry.register(CreditCardStrategy())
        registry.register(PayPalStrategy())
        registry.register(CryptoStrategy())

        # 3. التنفيذ
        request = PaymentRequest(amount=100, method="credit_card")
        result = await registry.execute(request)

        if result:
            print(f"الدفع نجح: {result}")
        else:
            print("لا توجد استراتيجية مناسبة")

    Complexity Analysis (CS61):
        - register(): O(n log n) حيث n عدد الاستراتيجيات (بسبب الترتيب)
        - execute(): O(n) في أسوأ الحالات (تجربة جميع الاستراتيجيات)
        - get_strategies(): O(n) - نسخ القائمة
        - clear(): O(1) - مسح القائمة

    Thread Safety:
        ⚠️ غير آمن للخيوط افتراضياً (Not thread-safe by default)
        💡 استخدم asyncio.Lock إذا كنت تشارك السجل بين tasks متعددة
    """

    def __init__(self) -> None:
        """
        تهيئة سجل الاستراتيجيات (Initialize the strategy registry).

        يُنشئ قائمة فارغة لتخزين الاستراتيجيات المسجلة.
        الاستراتيجيات ستُرتب تلقائياً حسب الأولوية عند التسجيل.

        Complexity: O(1)
        """
        self._strategies: list[Strategy[TInput, TOutput]] = []

    def register(self, strategy: Strategy[TInput, TOutput]) -> None:
        """
        تسجيل استراتيجية جديدة (Register a new strategy).

        الاستراتيجيات تُرتب تلقائياً حسب الأولوية (الأعلى أولاً).
        هذا يضمن أن الاستراتيجيات الأكثر تحديداً أو أهمية
        تُجرّب قبل الاستراتيجيات العامة أو الاحتياطية.

        Args:
            strategy: الاستراتيجية المراد تسجيلها

        Example:
            # تسجيل استراتيجيات متعددة
            registry.register(HighPriorityStrategy())  # priority=100
            registry.register(MediumPriorityStrategy())  # priority=50
            registry.register(LowPriorityStrategy())  # priority=10
            registry.register(FallbackStrategy())  # priority=0

            # سيتم تجربتها بالترتيب: 100 → 50 → 10 → 0

        Side Effects:
            - تُضاف الاستراتيجية للقائمة الداخلية
            - تُرتب القائمة حسب الأولوية (descending)
            - يُسجّل حدث في Logger للتتبع

        Complexity: O(n log n) حيث n = عدد الاستراتيجيات المسجلة
        """
        self._strategies.append(strategy)
        # ترتيب تنازلي حسب الأولوية (أعلى أولوية أولاً)
        self._strategies.sort(key=lambda s: s.priority, reverse=True)
        
        logger.debug(
            f"تم تسجيل الاستراتيجية: {strategy.__class__.__name__} "
            f"(الأولوية={strategy.priority})",
            extra={
                "strategy_class": strategy.__class__.__name__,
                "priority": strategy.priority,
                "total_strategies": len(self._strategies)
            }
        )

    async def execute(self, context: TInput) -> TOutput | None:
        """
        تنفيذ أول استراتيجية يمكنها معالجة السياق.

        الاستراتيجيات تُقيّم بترتيب الأولوية (الأعلى أولاً).
        أول استراتيجية تُرجع True من can_handle() سيتم تنفيذها.

        آلية العمل (Execution Flow):
        1. المرور على الاستراتيجيات حسب الأولوية
        2. استدعاء can_handle() للتحقق من القدرة على المعالجة
        3. إذا True، استدعاء execute() وإرجاع النتيجة
        4. إذا حدث خطأ، تسجيله والانتقال للاستراتيجية التالية
        5. إذا لم تنجح أي استراتيجية، إرجاع None

        معالجة النتائج المختلفة:
        - AsyncGenerator: يُرجع كما هو (للبث التدريجي)
        - Coroutine: يُنتظر تلقائياً (await)
        - قيمة عادية: تُرجع مباشرة

        Args:
            context: سياق المدخلات للمعالجة

        Returns:
            TOutput | None: 
                - نتيجة الاستراتيجية الأولى الناجحة
                - None إذا لم تتمكن أي استراتيجية من المعالجة

        Example (Coroutine Result):
            result = await registry.execute(context)
            if result:
                print(f"النتيجة: {result}")
            else:
                print("لا توجد استراتيجية مناسبة")

        Example (Async Generator Result):
            result = await registry.execute(context)
            if result:
                async for chunk in result:
                    print(f"جزء: {chunk}")

        Error Handling:
            - يُسجّل الأخطاء في Logger
            - يستمر في تجربة الاستراتيجيات التالية
            - لا يُوقف التنفيذ عند فشل استراتيجية واحدة

        Logging:
            - معلومات: استراتيجية تم تنفيذها بنجاح
            - تحذير: لا توجد استراتيجية مناسبة
            - خطأ: فشل تنفيذ استراتيجية (مع التفاصيل)

        Complexity: 
            - Best Case: O(1) - الاستراتيجية الأولى تنجح
            - Average Case: O(k) حيث k = عدد الاستراتيجيات المُجربة
            - Worst Case: O(n) - جميع الاستراتيجيات تفشل
        """
        for strategy in self._strategies:
            try:
                # التحقق من قدرة الاستراتيجية على المعالجة
                if await strategy.can_handle(context):
                    logger.debug(
                        f"تنفيذ الاستراتيجية: {strategy.__class__.__name__}",
                        extra={
                            "strategy_class": strategy.__class__.__name__,
                            "priority": strategy.priority
                        }
                    )
                    
                    # تنفيذ الاستراتيجية
                    # لا نستخدم await هنا لأن النتيجة قد تكون async generator
                    result = strategy.execute(context)
                    
                    # معالجة أنواع النتائج المختلفة
                    
                    # 1. Async Generator - إرجاع مباشر للبث التدريجي
                    if inspect.isasyncgen(result):
                        logger.debug(
                            f"إرجاع async generator من {strategy.__class__.__name__}"
                        )
                        return result
                    
                    # 2. Coroutine - انتظار النتيجة
                    if inspect.iscoroutine(result):
                        logger.debug(
                            f"انتظار coroutine من {strategy.__class__.__name__}"
                        )
                        result = await result
                    
                    # 3. قيمة عادية - إرجاع مباشر
                    logger.info(
                        f"✅ نجح تنفيذ: {strategy.__class__.__name__}",
                        extra={
                            "strategy_class": strategy.__class__.__name__,
                            "result_type": type(result).__name__
                        }
                    )
                    return result
                    
            except Exception as e:
                # تسجيل الخطأ والاستمرار في المحاولة
                logger.error(
                    f"❌ فشلت الاستراتيجية {strategy.__class__.__name__}: {e}",
                    exc_info=True,
                    extra={
                        "strategy_class": strategy.__class__.__name__,
                        "error_type": type(e).__name__,
                        "error_message": str(e)
                    }
                )
                # الاستمرار للاستراتيجية التالية
                continue

        # لم تنجح أي استراتيجية
        logger.warning(
            f"⚠️ لم يتم العثور على استراتيجية لمعالجة السياق: {context}",
            extra={
                "context_type": type(context).__name__,
                "total_strategies_tried": len(self._strategies)
            }
        )
        return None

    def get_strategies(self) -> list[Strategy[TInput, TOutput]]:
        """
        الحصول على جميع الاستراتيجيات المسجلة.

        Returns:
            list: نسخة من قائمة الاستراتيجيات (مرتبة حسب الأولوية)

        Note:
            تُرجع نسخة من القائمة (defensive copy) لمنع التعديل
            الخارجي على البنية الداخلية للسجل.

        Example:
            strategies = registry.get_strategies()
            for strategy in strategies:
                print(f"{strategy.__class__.__name__}: {strategy.priority}")

        Complexity: O(n) - نسخ القائمة
        """
        return self._strategies.copy()

    def clear(self) -> None:
        """
        مسح جميع الاستراتيجيات المسجلة (Clear all registered strategies).

        يُستخدم عادة في:
        - إعادة تكوين السجل (Reconfiguration)
        - الاختبارات (Testing - cleanup)
        - إعادة التهيئة الديناميكية (Dynamic reinitialization)

        Side Effects:
            - تُفرغ قائمة الاستراتيجيات تماماً
            - يُسجّل حدث في Logger

        Example:
            registry.clear()
            assert len(registry.get_strategies()) == 0

        Complexity: O(1)
        """
        self._strategies.clear()
        logger.debug(
            "تم مسح جميع الاستراتيجيات من السجل",
            extra={"action": "clear_all_strategies"}
        )

