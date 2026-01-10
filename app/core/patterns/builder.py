"""
نمط البناء السلس (Fluent Builder Pattern) - تطبيق احترافي
==============================================================

يوفر هذا الموديول فئة أساسية عامة لتطبيق نمط البناء (Builder Pattern)
مع واجهة سلسة لبناء كائنات معقدة بطريقة نظيفة وقابلة للقراءة.

المبادئ المطبقة (Applied Principles):
--------------------------------------
✅ Harvard CS50 2025:
   - Type Safety: استخدام Generic[T] للأمان الكامل للأنواع
   - Clean Code: كود نظيف وواضح وسهل القراءة
   - Documentation: توثيق شامل باللغة العربية والإنجليزية

✅ Berkeley CS61 (SICP):
   - Abstraction Barriers: فصل التعريف عن التطبيق
   - Data-Directed Programming: استخدام الأنواع العامة (Generics)
   - Higher-Order Procedures: البناء كعملية من مستوى أعلى

✅ SOLID Principles:
   - Single Responsibility: مسؤولية واحدة فقط (البناء)
   - Open/Closed: مفتوح للتوسع، مغلق للتعديل
   - Liskov Substitution: يمكن استبدال أي بناء بالفئة الأساسية
   - Dependency Inversion: الاعتماد على التجريد وليس التنفيذ

الاستخدام (Usage):
------------------
    from app.core.patterns.builder import FluentBuilder
    from dataclasses import dataclass

    @dataclass
    class Product:
        name: str
        price: float
        category: str = "general"

    class ProductBuilder(FluentBuilder[Product]):
        def __init__(self):
            super().__init__()
            self._name: str = ""
            self._price: float = 0.0
            self._category: str = "general"

        def reset(self) -> None:
            '''إعادة تعيين البناء إلى الحالة الأولية'''
            self._name = ""
            self._price = 0.0
            self._category = "general"

        def with_name(self, name: str) -> 'ProductBuilder':
            '''تعيين اسم المنتج'''
            self._name = name
            return self  # السلاسة (Fluency)

        def with_price(self, price: float) -> 'ProductBuilder':
            '''تعيين سعر المنتج'''
            if price < 0:
                raise ValueError("السعر يجب أن يكون موجباً")
            self._price = price
            return self

        def with_category(self, category: str) -> 'ProductBuilder':
            '''تعيين فئة المنتج'''
            self._category = category
            return self

        def build(self) -> Product:
            '''بناء المنتج النهائي'''
            if not self._name:
                raise ValueError("الاسم مطلوب")
            if self._price <= 0:
                raise ValueError("السعر يجب أن يكون أكبر من صفر")

            return Product(
                name=self._name,
                price=self._price,
                category=self._category
            )

    # مثال الاستخدام (Example):
    builder = ProductBuilder()
    product = (builder
        .with_name("Laptop")
        .with_price(999.99)
        .with_category("Electronics")
        .build()
    )

الفوائد (Benefits):
-------------------
✅ واجهة سلسة وقابلة للقراءة (Fluent and readable interface)
✅ التحقق من صحة البيانات أثناء البناء (Validation during construction)
✅ فصل منطق البناء عن الكائن نفسه (Separation of construction logic)
✅ إعادة استخدام البناء لعدة كائنات (Builder reusability)
✅ أمان كامل للأنواع مع Generics (Full type safety with Generics)

المراجع (References):
---------------------
- Gang of Four: Design Patterns (Builder Pattern)
- Martin Fowler: Refactoring, Chapter on Method Chaining
- Effective Java by Joshua Bloch: Item 2 - Consider a builder when faced with many constructor parameters
"""

from abc import ABC, abstractmethod
from typing import TypeVar

# متغير النوع العام (Generic Type Variable)
# يمثل نوع الكائن الذي سيتم بناؤه
T = TypeVar("T")


class FluentBuilder[T](ABC):
    """
    فئة أساسية مجردة للبنائين السلسين (Abstract Base Class for Fluent Builders).

    هذه الفئة توفر الهيكل الأساسي لتطبيق نمط البناء (Builder Pattern)
    مع واجهة سلسة (Fluent Interface) لتسلسل استدعاءات الدوال.

    المبدأ (Principle):
        يفصل نمط البناء عملية إنشاء كائن معقد عن تمثيله،
        بحيث يمكن لنفس عملية البناء إنشاء تمثيلات مختلفة.

    Generic Parameters:
        T: نوع الكائن الذي سيتم بناؤه (Type of object to be built)

    Abstract Methods:
        - reset(): إعادة تعيين البناء إلى الحالة الأولية
        - build(): بناء وإرجاع الكائن النهائي

    Example Implementation:
        class ConfigBuilder(FluentBuilder[Config]):
            def __init__(self):
                super().__init__()
                self._host: str = "localhost"
                self._port: int = 8000
                self._debug: bool = False

            def reset(self) -> None:
                '''إعادة التعيين'''
                self._host = "localhost"
                self._port = 8000
                self._debug = False

            def with_host(self, host: str) -> 'ConfigBuilder':
                '''تعيين المضيف'''
                self._host = host
                return self

            def with_port(self, port: int) -> 'ConfigBuilder':
                '''تعيين المنفذ'''
                if not (1 <= port <= 65535):
                    raise ValueError("منفذ غير صالح")
                self._port = port
                return self

            def with_debug(self, debug: bool = True) -> 'ConfigBuilder':
                '''تفعيل وضع التطوير'''
                self._debug = debug
                return self

            def build(self) -> Config:
                '''بناء الإعدادات'''
                return Config(
                    host=self._host,
                    port=self._port,
                    debug=self._debug
                )

        # الاستخدام (Usage):
        config = (ConfigBuilder()
            .with_host("0.0.0.0")
            .with_port(3000)
            .with_debug(True)
            .build()
        )

    Complexity Analysis (CS61):
        - Time: O(1) for all operations
        - Space: O(1) additional space per builder instance
        - Thread Safety: Not thread-safe by default (use locks if needed)

    Design Principles Applied:
        ✅ Abstraction Barrier: يخفي تفاصيل البناء عن المستخدم
        ✅ Separation of Concerns: يفصل منطق البناء عن الكائن
        ✅ Type Safety: يضمن الأمان الكامل للأنواع عبر Generics
    """

    def __init__(self) -> None:
        """
        تهيئة البناء (Initialize the builder).

        ملاحظة: الفئات الفرعية يجب أن تستدعي super().__init__()
        وتهيئ حالتها الخاصة.

        Complexity: O(1) - ثابت
        """
        pass

    @abstractmethod
    def reset(self) -> None:
        """
        إعادة تعيين البناء إلى الحالة الأولية (Reset builder to initial state).

        يجب على الفئات الفرعية تطبيق هذه الدالة لإعادة تعيين
        جميع الحقول الداخلية إلى قيمها الافتراضية.

        هذا يسمح بإعادة استخدام نفس البناء لإنشاء عدة كائنات
        بدون الحاجة لإنشاء بناء جديد في كل مرة.

        Raises:
            NotImplementedError: إذا لم يتم تطبيق الدالة في الفئة الفرعية

        Example:
            def reset(self) -> None:
                '''إعادة التعيين'''
                self._name = ""
                self._value = 0
                self._items.clear()

        Complexity: O(1) في معظم الحالات
        """
        pass

    @abstractmethod
    def build(self) -> T:
        """
        بناء وإرجاع الكائن النهائي (Build and return the final product).

        يجب على الفئات الفرعية تطبيق هذه الدالة لبناء الكائن
        النهائي من الحالة الداخلية للبناء.

        من المستحسن:
        1. التحقق من صحة جميع الحقول المطلوبة
        2. رفع استثناءات واضحة إذا كانت البيانات غير صالحة
        3. إنشاء وإرجاع كائن جديد (وليس مرجعاً للحالة الداخلية)

        Returns:
            T: الكائن المبني من النوع T

        Raises:
            ValueError: إذا كانت البيانات غير صالحة أو ناقصة
            NotImplementedError: إذا لم يتم تطبيق الدالة في الفئة الفرعية

        Example:
            def build(self) -> User:
                '''بناء المستخدم'''
                # التحقق من الصحة (Validation)
                if not self._email:
                    raise ValueError("البريد الإلكتروني مطلوب")
                if not self._name:
                    raise ValueError("الاسم مطلوب")

                # البناء (Construction)
                return User(
                    email=self._email,
                    name=self._name,
                    age=self._age
                )

        Complexity: يعتمد على تعقيد بناء الكائن (usually O(n) where n is number of fields)
        """
        pass
