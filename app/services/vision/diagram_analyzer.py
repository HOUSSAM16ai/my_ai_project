"""
محلل الرسوم البيانية (Diagram Analyzer).
========================================

يحلل ويفهم الرسوم البيانية والأشكال.
"""

import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

logger = logging.getLogger(__name__)


class DiagramType(StrEnum):
    """أنواع الرسوم البيانية."""

    FUNCTION_GRAPH = "function_graph"  # رسم دالة
    PROBABILITY_TREE = "probability_tree"  # شجرة احتمالات
    VENN_DIAGRAM = "venn_diagram"  # رسم فن
    GEOMETRIC_SHAPE = "geometric_shape"  # شكل هندسي
    COMPLEX_PLANE = "complex_plane"  # المستوى المركب
    TABLE = "table"  # جدول
    UNKNOWN = "unknown"


@dataclass
class DiagramAnalysis:
    """نتيجة تحليل رسم."""

    diagram_type: DiagramType
    description: str
    elements: list[str]
    mathematical_info: dict[str, Any]


class DiagramAnalyzer:
    """
    يحلل الرسوم البيانية التعليمية.
    """

    def analyze_from_description(
        self,
        description: str,
    ) -> DiagramAnalysis:
        """
        يحلل رسم من وصفه النصي.
        """
        desc_lower = description.lower()

        # تحديد نوع الرسم
        diagram_type = self._classify_diagram(desc_lower)

        # استخراج العناصر
        elements = self._extract_elements(description, diagram_type)

        # استخراج المعلومات الرياضية
        math_info = self._extract_math_info(description, diagram_type)

        return DiagramAnalysis(
            diagram_type=diagram_type,
            description=description,
            elements=elements,
            mathematical_info=math_info,
        )

    def _classify_diagram(self, description: str) -> DiagramType:
        """يصنف نوع الرسم."""

        if any(x in description for x in ["دالة", "function", "منحنى", "curve"]):
            return DiagramType.FUNCTION_GRAPH

        if any(x in description for x in ["شجرة", "tree", "فروع"]):
            return DiagramType.PROBABILITY_TREE

        if any(x in description for x in ["فن", "venn", "تقاطع", "اتحاد"]):
            return DiagramType.VENN_DIAGRAM

        if any(
            x in description
            for x in [
                "مثلث",
                "مربع",
                "دائرة",
                "هندسي",
                "triangle",
                "square",
                "circle",
                "geometric",
                "shape",
            ]
        ):
            return DiagramType.GEOMETRIC_SHAPE

        if any(x in description for x in ["مركب", "complex", "تخيلي", "imaginary"]):
            return DiagramType.COMPLEX_PLANE

        if any(x in description for x in ["جدول", "table", "صف", "عمود"]):
            return DiagramType.TABLE

        return DiagramType.UNKNOWN

    def _extract_elements(
        self,
        description: str,
        diagram_type: DiagramType,
    ) -> list[str]:
        """يستخرج عناصر الرسم."""

        elements = []

        if diagram_type == DiagramType.FUNCTION_GRAPH:
            # البحث عن نقاط خاصة
            import re

            points = re.findall(r"\([^)]+\)", description)
            elements.extend([f"نقطة: {p}" for p in points])

        elif diagram_type == DiagramType.PROBABILITY_TREE:
            # البحث عن الفروع
            elements.append("شجرة احتمالات")

        return elements

    def _extract_math_info(
        self,
        description: str,
        diagram_type: DiagramType,
    ) -> dict[str, Any]:
        """يستخرج المعلومات الرياضية."""

        info: dict[str, Any] = {}

        # البحث عن الأرقام
        import re

        numbers = re.findall(r"-?\d+\.?\d*", description)
        if numbers:
            info["numbers"] = [float(n) for n in numbers]

        return info

    def describe_for_ai(
        self,
        analysis: DiagramAnalysis,
    ) -> str:
        """يصيغ وصفاً للذكاء الاصطناعي."""

        parts = [
            f"نوع الرسم: {analysis.diagram_type.value}",
            f"الوصف: {analysis.description}",
        ]

        if analysis.elements:
            parts.append(f"العناصر: {', '.join(analysis.elements)}")

        if analysis.mathematical_info:
            parts.append(f"معلومات رياضية: {analysis.mathematical_info}")

        return "\n".join(parts)


# Singleton
_analyzer: DiagramAnalyzer | None = None


def get_diagram_analyzer() -> DiagramAnalyzer:
    """يحصل على محلل الرسوم."""
    global _analyzer
    if _analyzer is None:
        _analyzer = DiagramAnalyzer()
    return _analyzer
