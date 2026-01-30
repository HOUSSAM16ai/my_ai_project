"""
حل التمييز متعدد الأشكال (Polymorphic Discriminator Resolution)
---------------------------------------------------------------
هذه الوحدة تقدم حلاً احترافياً وعميقاً لمشكلة تعدد الأشكال في OpenAPI 3.1 و JSON Schema 2020-12.

المشكلة (The Problem):
----------------------
في OpenAPI 3.1، تم دمج JSON Schema 2020-12 بالكامل، مما يسمح باستخدام `oneOf` للتحقق من الأنواع.
ومع ذلك، تعتمد بعض المخططات على الكلمة المفتاحية `const` داخل كل نوع لتمييزه ضمنياً، بدلاً من استخدام
الكلمة المفتاحية الصريحة `discriminator` التي كانت شائعة في OAS 3.0.

السؤال 1: لماذا تفشل مولدات الكود (Code Generators) عند الاعتماد على `const` فقط؟
---------------------------------------------------------------------------------
الجواب يكمن في كيفية عمل المحللات (Parsers)، وخاصة المتدفقة (Streaming) وعالية الإنتاجية:
1.  **الغموض (Ambiguity)**: بدون `discriminator` صريح، يجب على المحلل تجربة كل مخطط في `oneOf`
    واحداً تلو الآخر (Trial and Error). هذا يعني محاولة إلغاء التسلسل (Deserialization) كـ `Dog`،
    وإذا فشل، المحاولة كـ `Cat`. هذه العملية مكلفة جداً (O(N) بدلاً من O(1)).
2.  **التدفق (Streaming)**: في المحللات المتدفقة (مثل Jackson في Java أو Serde في Rust)، تتم قراءة
    الرموز (Tokens) بالتسلسل. إذا جاء حقل التمييز (مثل `type`) في نهاية كائن JSON الكبير،
    فإن المحلل الذي يعتمد على `const` لا يمكنه تحديد الفئة المستهدفة إلا بعد قراءة كامل الكائن وحفظه
    في الذاكرة (Buffering)، مما يلغي فوائد التدفق ويستهلك الذاكرة.
3.  **توليد الكود**: المولدات (مثل openapi-generator) تحتاج إلى معرفة الفئة المستهدفة *قبل* بدء
    عملية التحليل لإنشاء الكائن الصحيح (Instantiation). وجود `discriminator` يسمح بإنشاء تعليمة `switch`
    بسيطة لتوجيه البيانات إلى الفئة الصحيحة فوراً.

السؤال 2: `unevaluatedProperties` مقابل `additionalProperties`
---------------------------------------------------------------
1.  **`additionalProperties: false` (OAS 3.0)**:
    - تعمل فقط على الخصائص المعرفة *معجمياً* (Lexically) في نفس المخطط.
    - عند استخدامها مع `allOf` أو `oneOf`، فإنها غالباً ما تفشل لأنها لا "ترى" الخصائص المعرفة
      في المخططات الفرعية المدمجة، مما يؤدي إما إلى رفض بيانات صالحة أو السماح ببيانات غير صالحة بشكل غير مقصود.
2.  **`unevaluatedProperties: false` (OAS 3.1)**:
    - أكثر ذكاءً وصرامة. تعمل بناءً على *التقييم الديناميكي* (Dynamic Evaluation).
    - إذا تم التحقق من خاصية بنجاح بواسطة *أي* مخطط فرعي (في `oneOf` أو `allOf`)، فإنها تعتبر "مُقيّمة".
    - تضمن هذه الكلمة المفتاحية أنه لا توجد أي خصائص متبقية في الكائن لم يتم التحقق منها بواسطة
      أي جزء من المخطط، مما يوفر صرامة حقيقية لتعدد الأشكال والتركيب (Composition).

الحل (The Solution):
--------------------
نستخدم `Annotated` مع `Field(discriminator=...)` من مكتبة Pydantic V2.
هذا يضمن توليد مخطط OpenAPI يحتوي على حقل `discriminator` الصريح، مما يحل مشاكل التوليد والأداء،
مع الاستفادة من ميزات التحقق القوية.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PolymorphicBaseModel(BaseModel):
    """
    نموذج أساسي يدعم تعدد الأشكال بشكل صريح وصارم.
    يستخدم ConfigDict لضمان الامتثال للمعايير.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        use_enum_values=True,
        # يضمن استخدام التمييز في المخطط الناتج
        json_schema_extra={"discriminator": {"propertyName": "type"}},
    )


class Pet(PolymorphicBaseModel):
    """
    الفئة الأساسية للحيوانات الأليفة.
    Note: removed ABC to avoid metaclass conflict with Pydantic's BaseModel.
    """

    name: str = Field(..., description="اسم الحيوان الأليف")
    # يجب تعريف حقل التمييز في الفئة الأساسية أو التأكد من وجوده في المشتقات
    type: str


class Dog(Pet):
    """
    نموذج الكلب، يمثل أحد الأشكال المتعددة.
    """

    type: Literal["dog"] = Field("dog", description="نوع الحيوان: كلب")
    bark: bool = Field(True, description="هل ينبح الكلب؟")


class Cat(Pet):
    """
    نموذج القط، يمثل الشكل الآخر.
    """

    type: Literal["cat"] = Field("cat", description="نوع الحيوان: قط")
    meow: bool = Field(True, description="هل يموء القط؟")


# تعريف النوع المتعدد الأشكال باستخدام Annotated و Discriminator
# هذا هو الجزء الجوهري الذي يحل المشكلة لمولدات الكود
PetUnion = Annotated[Dog | Cat, Field(discriminator="type")]


class PetOwner(BaseModel):
    """
    نموذج المالك الذي يحتوي على قائمة من الحيوانات متعددة الأشكال.
    """

    owner_name: str
    pets: list[PetUnion]

    @field_validator("pets", mode="before")
    @classmethod
    def validate_pet_discriminator(cls, value: object) -> object:
        """
        يتحقق من سلامة قيمة حقل التمييز قبل التحويل متعدد الأشكال.
        """
        if not isinstance(value, list):
            return value
        allowed_types = {"dog", "cat"}
        for item in value:
            if isinstance(item, dict):
                pet_type = item.get("type")
                if pet_type not in allowed_types:
                    raise ValueError("Input should be 'dog' or 'cat'")
        return value
