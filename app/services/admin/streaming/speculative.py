"""تنبؤات بسيطة لدعم ميزات التفريغ الاستباقي في البث."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SpeculativeDecoder:
    """يتوقع الرموز التالية اعتماداً على أنماط شائعة وسياق بسيط."""

    prediction_cache: dict[str, list[str]] = field(default_factory=dict)
    common_patterns: dict[str, list[str]] = field(
        default_factory=lambda: {
            "def ": ["function_name(", "class ", "method("],
            "import ": ["os", "sys", "json", "logging"],
            "from ": ["app", "fastapi", "typing"],
        }
    )

    def predict_next_tokens(self, current_text: str, count: int = 3) -> list[str]:
        """يُرجع الرموز المتوقعة التالية بناءً على النص الحالي."""

        for pattern, predictions in self.common_patterns.items():
            if current_text.endswith(pattern):
                return predictions[:count]

        words = current_text.split()
        if not words:
            return []

        last_word = words[-1].lower()
        if last_word in {"the", "a", "an"}:
            return ["next", "following", "best"][:count]
        if last_word in {"is", "are", "was", "were"}:
            return ["a", "the", "not"][:count]

        return []
