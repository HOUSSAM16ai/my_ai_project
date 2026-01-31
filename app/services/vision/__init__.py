"""
خدمات الرؤية (Vision Services).
================================

تتضمن:
- MultiModalProcessor: معالجة الصور والوسائط
- EquationDetector: كشف المعادلات الرياضية
- DiagramAnalyzer: تحليل الرسوم البيانية

تتكامل مع:
- LlamaIndex: لربط المحتوى بالمعرفة
- OpenAI Vision API: لتحليل الصور
"""

from app.services.vision.diagram_analyzer import (
    DiagramAnalysis,
    DiagramAnalyzer,
    DiagramType,
    get_diagram_analyzer,
)
from app.services.vision.equation_detector import (
    EquationDetector,
    get_equation_detector,
)
from app.services.vision.multimodal_processor import (
    ImageAnalysis,
    MultiModalProcessor,
    get_multimodal_processor,
)

__all__ = [
    "DiagramAnalysis",
    # Diagram Analyzer
    "DiagramAnalyzer",
    "DiagramType",
    # Equation Detector
    "EquationDetector",
    "ImageAnalysis",
    # MultiModal Processor
    "MultiModalProcessor",
    "get_diagram_analyzer",
    "get_equation_detector",
    "get_multimodal_processor",
]
