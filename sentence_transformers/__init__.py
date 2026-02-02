"""
تنفيذ مبسط لحزمة sentence_transformers لتوافق الاختبارات.

يوفر صنف SentenceTransformer مع encode يعيد متجهًا ثابتًا.
"""

from __future__ import annotations


class _Vector:
    """متجه مبسط يطابق واجهة numpy عبر tolist."""

    def __init__(self, values: list[float]) -> None:
        self._values = values

    def tolist(self) -> list[float]:
        """يعيد القيم كقائمة."""
        return list(self._values)


class SentenceTransformer:
    """بديل مبسط للنموذج النصي."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def encode(self, text: str) -> _Vector:
        """يعيد متجهًا ثابتًا لغرض الاختبارات."""
        return _Vector([0.0, 0.0, 0.0])


class CrossEncoder:
    """مُرمّز تبادلي مبسط يدعم predict للاختبارات."""

    def __init__(self, model_name: str) -> None:
        self.model_name = model_name

    def predict(self, pairs: list[list[str]]) -> list[float]:
        """يعيد درجات ثابتة بنفس طول الأزواج."""
        return [0.0 for _ in pairs]


__all__ = ["SentenceTransformer", "CrossEncoder"]
