# app/services/overmind/domain/context.py
"""
سياق التعاون (Collaboration Context).
---------------------------------------------------------
تنفيذ ملموس لبروتوكول CollaborationContext لإدارة الحالة المشتركة
بين وكلاء "مجلس الحكمة" (Council of Wisdom).

المعايير:
- CS50 2025 Strict Mode.
- توثيق "Legendary" باللغة العربية.
"""

from typing import TypeAlias

from app.core.protocols import CollaborationContext


JsonValue: TypeAlias = object
SharedMemory: TypeAlias = dict[str, JsonValue]


class InMemoryCollaborationContext(CollaborationContext):
    """
    سياق تعاوني في الذاكرة (In-Memory).

    يستخدم لتمرير المعلومات والحالة بين الوكلاء خلال دورة حياة المهمة الواحدة.
    """

    def __init__(self, initial_data: SharedMemory | None = None) -> None:
        self.shared_memory: SharedMemory = initial_data or {}

    def update(self, key: str, value: JsonValue) -> None:
        """
        تحديث قيمة في الذاكرة المشتركة.

        Args:
            key (str): المفتاح.
            value (object): القيمة الجديدة.
        """
        self.shared_memory[key] = value

    def get(self, key: str) -> JsonValue | None:
        """
        استرجاع قيمة من الذاكرة المشتركة.

        Args:
            key (str): المفتاح.

        Returns:
            object | None: القيمة المطلوبة أو None إذا لم تكن موجودة.
        """
        return self.shared_memory.get(key)

    def add_trace(self, entry: dict[str, JsonValue]) -> None:
        """
        إضافة سجل تنسيق لعمليات الوكلاء.

        Args:
            entry: سجل يحتوي على بيانات التزامن (مثل المرحلة/الوكيل/الحالة).
        """
        trace = self.shared_memory.get("coordination_trace")
        if not isinstance(trace, list):
            trace = []
            self.shared_memory["coordination_trace"] = trace
        trace.append(entry)

    def get_trace(self) -> list[dict[str, JsonValue]]:
        """
        استرجاع سجل تنسيق الوكلاء.

        Returns:
            list[dict[str, JsonValue]]: قائمة سجلات التنسيق.
        """
        trace = self.shared_memory.get("coordination_trace")
        if isinstance(trace, list):
            return [entry for entry in trace if isinstance(entry, dict)]
        return []
