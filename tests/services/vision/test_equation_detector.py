from app.services.vision.equation_detector import (
    EquationDetector,
    get_equation_detector,
)


def test_singleton_instance():
    det1 = get_equation_detector()
    det2 = get_equation_detector()
    assert det1 is det2
    assert isinstance(det1, EquationDetector)


def test_extract_equations():
    detector = EquationDetector()
    text = "Solve for x in $2x + 1 = 5$ or using blocks $$E = mc^2$$."
    equations = detector.extract_equations(text)
    assert "$2x + 1 = 5$" in equations
    assert "$$E = mc^2$$" in equations


def test_extract_equations_math_symbols():
    detector = EquationDetector()
    text = "Find the sum ∑ and integral ∫."
    equations = detector.extract_equations(text)
    assert "∑" in equations or any("∑" in eq for eq in equations)
    assert "∫" in equations or any("∫" in eq for eq in equations)


def test_classify_integral():
    detector = EquationDetector()
    assert detector.classify_equation("∫ f(x) dx") == "تكامل"
    assert detector.classify_equation("Integral of x^2") == "تكامل"


def test_classify_derivative():
    detector = EquationDetector()
    assert detector.classify_equation("f'(x) = 2x") == "اشتقاق"
    assert detector.classify_equation("derivative of sin(x)") == "اشتقاق"


def test_classify_limits():
    detector = EquationDetector()
    assert detector.classify_equation("lim x->0") == "نهايات"
    assert detector.classify_equation("نهاية الدالة") == "نهايات"


def test_classify_complex():
    detector = EquationDetector()
    assert detector.classify_equation("z = a + bi") == "أعداد مركبة"


def test_classify_probability():
    detector = EquationDetector()
    assert detector.classify_equation("P(A|B) = 0.5") == "احتمالات"


def test_classify_sequence():
    detector = EquationDetector()
    assert detector.classify_equation("u_n = u_{n-1} + 1") == "متتاليات"


def test_classify_general():
    detector = EquationDetector()
    assert detector.classify_equation("x + y = 10") == "عام"


def test_to_latex():
    detector = EquationDetector()
    eq = "Area = π * r^2"
    latex = detector.to_latex(eq)
    assert "\\pi" in latex

    eq2 = "α + β"
    assert "\\alpha" in detector.to_latex(eq2)
    assert "\\beta" in detector.to_latex(eq2)
