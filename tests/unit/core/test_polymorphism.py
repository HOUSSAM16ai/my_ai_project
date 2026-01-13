import pytest
from pydantic import ValidationError
from app.core.polymorphism import PetOwner, Dog, Cat, PetUnion

def test_polymorphic_deserialization():
    """
    اختبار قدرة النظام على إلغاء تسلسل قائمة متعددة الأشكال (Dogs and Cats)
    بناءً على حقل التمييز 'type'.
    """
    data = {
        "owner_name": "Jules",
        "pets": [
            {"type": "dog", "name": "Buddy", "bark": True},
            {"type": "cat", "name": "Whiskers", "meow": True},
            {"type": "dog", "name": "Rex", "bark": False}
        ]
    }

    owner = PetOwner(**data)

    assert len(owner.pets) == 3
    assert isinstance(owner.pets[0], Dog)
    assert owner.pets[0].name == "Buddy"
    assert owner.pets[0].bark is True

    assert isinstance(owner.pets[1], Cat)
    assert owner.pets[1].name == "Whiskers"
    assert owner.pets[1].meow is True

    assert isinstance(owner.pets[2], Dog)
    assert owner.pets[2].name == "Rex"
    assert owner.pets[2].bark is False

def test_invalid_discriminator():
    """
    التحقق من أن قيمة التمييز غير المعروفة تؤدي إلى خطأ في التحقق.
    """
    data = {
        "owner_name": "ErrorUser",
        "pets": [
            {"type": "bird", "name": "Tweety"} # bird غير معرف
        ]
    }

    with pytest.raises(ValidationError) as excinfo:
        PetOwner(**data)

    # يجب أن يشير الخطأ إلى مشكلة في التمييز أو عدم تطابق أي من الأنواع
    assert "Input should be 'dog'" in str(excinfo.value) or "Input should be 'cat'" in str(excinfo.value)

def test_json_schema_generation():
    """
    التحقق من أن مخطط JSON المولد يحتوي على كلمة 'discriminator' المفتاحية
    لضمان التوافق مع مولدات الكود.
    """
    schema = PetOwner.model_json_schema()

    # الوصول إلى تعريف PetUnion في المخطط
    # ملاحظة: في Pydantic V2، التعريفات تكون في $defs
    defs = schema.get("$defs", {})

    # نبحث عن المخطط الذي يحتوي على oneOf
    # PetUnion قد لا يكون له اسم مباشر في $defs إذا تم استخدامه مباشرة،
    # لكن Dog و Cat سيكونان هناك.
    # ومع ذلك، الحقل 'pets' سيشير إلى مخطط يحتوي على discriminator.

    pets_prop = schema["properties"]["pets"]
    item_schema = pets_prop["items"]

    # قد يكون مرجعاً $ref
    if "$ref" in item_schema:
        ref_name = item_schema["$ref"].split("/")[-1]
        union_schema = defs[ref_name]
    else:
        union_schema = item_schema

    # يجب أن يحتوي المخطط على 'discriminator'
    assert "discriminator" in union_schema
    assert union_schema["discriminator"]["propertyName"] == "type"

    # التحقق من oneOf
    assert "oneOf" in union_schema
    assert len(union_schema["oneOf"]) == 2
