"""
اختبار معرفة المؤسس في نظام المحادثة.

يتحقق هذا الاختبار من أن:
1. معلومات المؤسس تُحقن في سياق المحادثة
2. الرسائل تحتوي على معلومات الهوية الصحيحة
3. التنسيق صحيح ودقيق
"""

import pytest

from app.services.chat.handlers.strategy_handlers import DefaultChatHandler


class TestFounderIdentityInChat:
    """اختبارات معرفة المؤسس في المحادثة."""

    def setup_method(self):
        """إعداد الاختبار."""
        self.handler = DefaultChatHandler()

    def test_handler_has_identity(self):
        """اختبار: المعالج يحتوي على نظام الهوية."""
        assert hasattr(self.handler, "_identity")
        assert self.handler._identity is not None

    def test_add_identity_context_to_empty_messages(self):
        """اختبار: إضافة سياق الهوية إلى قائمة رسائل فارغة."""
        messages = []
        enhanced = self.handler._add_identity_context(messages)

        # يجب أن تحتوي على رسالة نظام واحدة على الأقل
        assert len(enhanced) >= 1
        assert enhanced[0]["role"] == "system"

        # يجب أن تحتوي رسالة النظام على معلومات المؤسس
        content = enhanced[0]["content"]
        assert "حسام بن مراح" in content
        assert "Houssam Benmerah" in content
        assert "1997-08-11" in content

    def test_add_identity_context_preserves_existing_messages(self):
        """اختبار: الحفاظ على الرسائل الموجودة."""
        messages = [
            {"role": "user", "content": "مرحباً"},
            {"role": "assistant", "content": "أهلاً بك"},
        ]
        enhanced = self.handler._add_identity_context(messages)

        # يجب أن تكون رسالة النظام في البداية + الرسائل الأصلية
        assert len(enhanced) == 3
        assert enhanced[0]["role"] == "system"
        assert enhanced[1]["role"] == "user"
        assert enhanced[2]["role"] == "assistant"

    def test_identity_context_contains_founder_info(self):
        """اختبار: سياق الهوية يحتوي على معلومات المؤسس الكاملة."""
        messages = []
        enhanced = self.handler._add_identity_context(messages)
        content = enhanced[0]["content"]

        # التحقق من وجود جميع العناصر المهمة
        assert "الاسم الكامل" in content or "حسام بن مراح" in content
        assert "Houssam" in content
        assert "Benmerah" in content
        assert "حسام" in content
        assert "بن مراح" in content
        assert "1997-08-11" in content or "11 أغسطس 1997" in content
        assert "المؤسس" in content
        assert "HOUSSAM16ai" in content

    def test_identity_context_with_existing_system_message(self):
        """اختبار: إضافة معلومات الهوية إلى رسالة نظام موجودة."""
        messages = [
            {"role": "system", "content": "أنت مساعد ذكي"},
            {"role": "user", "content": "من المؤسس؟"},
        ]
        enhanced = self.handler._add_identity_context(messages)

        # يجب أن يبقى عدد الرسائل كما هو
        assert len(enhanced) == 2
        assert enhanced[0]["role"] == "system"

        # يجب أن تحتوي رسالة النظام على المحتوى الأصلي + معلومات الهوية
        content = enhanced[0]["content"]
        assert "أنت مساعد ذكي" in content
        assert "حسام بن مراح" in content

    def test_founder_name_components_in_context(self):
        """اختبار: جميع مكونات اسم المؤسس موجودة."""
        messages = []
        enhanced = self.handler._add_identity_context(messages)
        content = enhanced[0]["content"]

        # الاسم الأول بالعربية والإنجليزية
        assert "حسام" in content
        assert "Houssam" in content

        # اللقب بالعربية والإنجليزية
        assert "بن مراح" in content
        assert "Benmerah" in content

    def test_founder_role_in_context(self):
        """اختبار: دور المؤسس موجود في السياق."""
        messages = []
        enhanced = self.handler._add_identity_context(messages)
        content = enhanced[0]["content"]

        # يجب أن يحتوي على دور المؤسس
        assert "المؤسس" in content or "المهندس الرئيسي" in content
        assert "Creator" in content or "Lead Architect" in content

    def test_founder_github_in_context(self):
        """اختبار: معلومات GitHub للمؤسس موجودة."""
        messages = []
        enhanced = self.handler._add_identity_context(messages)
        content = enhanced[0]["content"]

        # يجب أن يحتوي على اسم المستخدم في GitHub
        assert "HOUSSAM16ai" in content

    def test_overmind_identity_in_context(self):
        """اختبار: معلومات Overmind نفسه موجودة."""
        messages = []
        enhanced = self.handler._add_identity_context(messages)
        content = enhanced[0]["content"]

        # يجب أن يحتوي على معلومات عن Overmind
        assert "Overmind" in content or "العقل المدبر" in content

    def test_context_has_clear_instructions(self):
        """اختبار: السياق يحتوي على تعليمات واضحة للإجابة عن أسئلة المؤسس."""
        messages = []
        enhanced = self.handler._add_identity_context(messages)
        content = enhanced[0]["content"]

        # يجب أن يحتوي على تعليمات عن كيفية الإجابة
        assert "مؤسس" in content.lower() or "founder" in content.lower()


class TestFounderIdentityIntegration:
    """اختبارات تكامل معرفة المؤسس."""

    def setup_method(self):
        """إعداد الاختبار."""
        self.handler = DefaultChatHandler()

    def test_identity_injection_is_consistent(self):
        """اختبار: حقن الهوية متسق في كل مرة."""
        messages1 = []
        messages2 = []

        enhanced1 = self.handler._add_identity_context(messages1)
        enhanced2 = self.handler._add_identity_context(messages2)

        # يجب أن يكون المحتوى متطابقاً
        assert enhanced1[0]["content"] == enhanced2[0]["content"]

    def test_multiple_calls_dont_duplicate_context(self):
        """اختبار: المكالمات المتعددة لا تكرر السياق."""
        messages = []
        enhanced1 = self.handler._add_identity_context(messages)
        enhanced2 = self.handler._add_identity_context(enhanced1)

        # يجب ألا يتضاعف المحتوى
        # (عدد مرات ظهور الاسم يجب أن يكون محدوداً)
        content = enhanced2[0]["content"]
        count = content.count("حسام بن مراح")

        # يجب ألا يظهر الاسم أكثر من مرتين (واحدة في الاسم الكامل، واحدة محتملة في سياق آخر)
        assert count <= 3


if __name__ == "__main__":
    # تشغيل الاختبارات مباشرة
    pytest.main([__file__, "-v"])
