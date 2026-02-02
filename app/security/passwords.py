"""
سياق كلمات المرور الموحّد (Unified Password Context).

يوفر هذا الملف سياق التشفير المركزي لكلمات المرور بحيث يتم استخدامه
عبر جميع طبقات التطبيق دون تسريب المنطق الأمني إلى النماذج.
"""
import hashlib
import importlib
import importlib.util


class _FallbackCryptContext:
    """سياق احتياطي لتوليد والتحقق من التجزئة عند غياب passlib."""

    def hash(self, plain: str) -> str:
        """ينشئ تجزئة مبسطة تعتمد على SHA256 لتأمين الاختبارات."""
        digest = hashlib.sha256(plain.encode("utf-8")).hexdigest()
        return f"sha256${digest}"

    def verify(self, plain: str, hashed: str) -> bool:
        """يتحقق من مطابقة كلمة المرور مع التجزئة المبسطة."""
        if not hashed.startswith("sha256$"):
            return False
        expected = self.hash(plain)
        return expected == hashed


def _build_password_context() -> object:
    """يبني سياق كلمات المرور باستخدام passlib إن كان متاحاً."""
    if importlib.util.find_spec("passlib") is None:
        return _FallbackCryptContext()
    passlib_module = importlib.import_module("passlib.context")
    return passlib_module.CryptContext(
        schemes=["argon2", "bcrypt", "pbkdf2_sha256", "sha256_crypt"],
        deprecated="auto",
    )


pwd_context = _build_password_context()
