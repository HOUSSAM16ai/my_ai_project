"""
كاشف المعادلات (Equation Detector).
===================================

يكشف ويحلل المعادلات الرياضية.
"""

import logging
import re

logger = logging.getLogger(__name__)


class EquationDetector:
    """
    يكشف المعادلات الرياضية من النصوص والصور.
    """
    
    # أنماط المعادلات الشائعة
    EQUATION_PATTERNS = [
        r'\$[^\$]+\$',                    # LaTeX inline: $...$
        r'\$\$[^\$]+\$\$',                # LaTeX block: $$...$$
        r'\\[\(\[][^\]]+\\[\)\]]',        # LaTeX: \( \) or \[ \]
        r'[a-zA-Z]+\s*=\s*[^\n]+',        # مثل: f(x) = ...
        r'\d+\s*[\+\-\×\÷]\s*\d+',        # عمليات حسابية
        r'∫|∑|∏|√|∞',                     # رموز رياضية
    ]
    
    def extract_equations(self, text: str) -> list[str]:
        """يستخرج المعادلات من نص."""
        
        equations = []
        
        for pattern in self.EQUATION_PATTERNS:
            matches = re.findall(pattern, text)
            equations.extend(matches)
        
        return list(set(equations))  # إزالة التكرار
    
    def classify_equation(self, equation: str) -> str:
        """يصنف نوع المعادلة."""
        
        eq_lower = equation.lower()
        
        if any(x in eq_lower for x in ['∫', 'integral', 'تكامل']):
            return "تكامل"
        
        if any(x in eq_lower for x in ['lim', 'نهاية', '→']):
            return "نهايات"
        
        if any(x in eq_lower for x in ["'", 'derivative', 'اشتقاق']):
            return "اشتقاق"
        
        if any(x in eq_lower for x in ['z', 'i', 'مركب']):
            return "أعداد مركبة"
        
        if any(x in eq_lower for x in ['p(', 'probability', 'احتمال']):
            return "احتمالات"
        
        if any(x in eq_lower for x in ['u_n', 'متتالية', 'sequence']):
            return "متتاليات"
        
        return "عام"
    
    def to_latex(self, equation: str) -> str:
        """يحول معادلة لتنسيق LaTeX."""
        
        # تحويلات أساسية
        conversions = {
            '×': r'\times',
            '÷': r'\div',
            '√': r'\sqrt',
            '∞': r'\infty',
            '∫': r'\int',
            '∑': r'\sum',
            '∏': r'\prod',
            'π': r'\pi',
            'α': r'\alpha',
            'β': r'\beta',
            'θ': r'\theta',
        }
        
        result = equation
        for symbol, latex in conversions.items():
            result = result.replace(symbol, latex)
        
        return result


# Singleton
_detector: EquationDetector | None = None


def get_equation_detector() -> EquationDetector:
    """يحصل على كاشف المعادلات."""
    global _detector
    if _detector is None:
        _detector = EquationDetector()
    return _detector
