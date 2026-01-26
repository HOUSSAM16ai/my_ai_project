import unittest

from app.core.governance.schema_evolution import (
    ChangeType,
    ContractEvolutionChecker,
    ResolutionScope,
    SchemaResolver,
)
from app.core.types import JSONDict


class TestSchemaEvolution(unittest.TestCase):
    def test_dynamic_ref_resolution(self):
        """
        اختبار القدرة على حل $dynamicRef بشكل صحيح.
        يحاكي المثال القياسي حيث يغير النطاق قيمة المرجع.
        """
        # تعريف مخطط أساسي يستخدم dynamicRef
        base_schema: JSONDict = {
            "$id": "https://example.com/base",
            "$dynamicAnchor": "meta",
            "type": "string",  # Default base type
            "definitions": {"default": {"$dynamicRef": "#meta"}},
        }

        # تعريف مخطط موسع يغير المرساة
        extended_schema: JSONDict = {
            "$id": "https://example.com/extended",
            "$dynamicAnchor": "meta",
            "type": "integer",  # Extended type overrides to integer
            "allOf": [
                base_schema
            ],  # In a real resolver we'd merge, but here we construct manually for test logic
        }

        # نحن نختبر Resolver مباشرة
        # السيناريو: نحن داخل "extended_schema" ونحاول حل مرجع يشير إلى "#meta"

        resolver = SchemaResolver(extended_schema)
        scope = ResolutionScope()

        # 1. دفع المخطط الموسع إلى النطاق (هو الأبعد/الخارجي)
        scope = scope.push("extended", extended_schema)

        # 2. دفع المخطط الأساسي (الداخلي)
        scope = scope.push("base", base_schema)

        # الآن نحاول حل "$dynamicRef": "#meta" الموجود في base_schema
        # حسب المعيار، يجب أن يجد "meta" الموجود في "extended_schema" (الأبعد)

        resolved = resolver._resolve_dynamic_ref("#meta", scope)

        self.assertEqual(resolved.get("type"), "integer")
        self.assertNotEqual(resolved.get("type"), "string")

    def test_breaking_change_detection(self):
        """اختبار اكتشاف التغييرات الكاسرة."""
        old_schema: JSONDict = {
            "type": "object",
            "required": ["id"],
            "properties": {"id": {"type": "integer"}, "name": {"type": "string"}},
        }

        new_schema: JSONDict = {
            "type": "object",
            "required": ["id", "new_required_field"],  # Breaking: New required field
            "properties": {
                "id": {"type": "string"},  # Breaking: Type change int -> string
                # "name" removed -> Breaking
                "new_required_field": {"type": "boolean"},
            },
        }

        checker = ContractEvolutionChecker()
        issues = checker.check_evolution(old_schema, new_schema)

        # نتوقع 3 مشاكل كاسرة:
        # 1. تغيير نوع id
        # 2. حذف name
        # 3. إضافة new_required_field

        breaking_issues = [i for i in issues if i.change_type == ChangeType.BREAKING]
        self.assertEqual(len(breaking_issues), 3)

        messages = [i.message for i in breaking_issues]
        self.assertTrue(any("Type changed" in m for m in messages))
        self.assertTrue(any("Property 'name' removed" in m for m in messages))
        self.assertTrue(any("Property 'new_required_field' became required" in m for m in messages))

    def test_recursion_handling(self):
        """اختبار عدم الدخول في حلقة لانهائية مع المخططات العودية."""
        recursive_schema: JSONDict = {"type": "object", "properties": {"self": {"$ref": "#"}}}

        # مقارنة المخطط بنفسه يجب أن لا تسبب StackOverflow
        checker = ContractEvolutionChecker()
        issues = checker.check_evolution(recursive_schema, recursive_schema)

        self.assertEqual(len(issues), 0)


if __name__ == "__main__":
    unittest.main()
