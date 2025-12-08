import pytest
from app.services.ai_intelligent_testing import (
    AITestGenerator,
    SmartTestSelector,
    CoverageOptimizer,
    TestCase,
    TestType,
    CodeAnalysis
)

SAMPLE_CODE = """
import math

def calculate_area(radius: float) -> float:
    \"\"\"Calculate area of a circle\"\"\"
    if radius < 0:
        raise ValueError("Radius cannot be negative")
    return math.pi * radius * radius

class Calculator:
    def add(self, a: int, b: int) -> int:
        return a + b
"""

@pytest.fixture
def generator():
    return AITestGenerator()

def test_analyze_code(generator):
    """Test analyzing code structure."""
    analysis = generator.analyze_code(SAMPLE_CODE, "test_file.py")

    assert isinstance(analysis, CodeAnalysis)
    assert analysis.file_path == "test_file.py"

    # Check functions
    # ast.walk visits all nodes, so it finds 'calculate_area' AND 'add' (inside Calculator)
    assert len(analysis.functions) == 2
    func_names = [f["name"] for f in analysis.functions]
    assert "calculate_area" in func_names
    assert "add" in func_names

    calc_area_func = next(f for f in analysis.functions if f["name"] == "calculate_area")
    assert calc_area_func["params"][0]["name"] == "radius"

    # Check classes
    assert len(analysis.classes) == 1
    assert analysis.classes[0]["name"] == "Calculator"
    assert len(analysis.classes[0]["methods"]) == 1

    # Check dependencies
    assert "math" in analysis.dependencies

    # Check edge cases
    assert len(analysis.edge_cases) > 0
    # The edge case description contains the function name, not necessarily the param name
    assert any("calculate_area" in case for case in analysis.edge_cases)

def test_analyze_code_syntax_error(generator):
    """Test analyzing invalid code."""
    analysis = generator.analyze_code("def broken_code(:", "broken.py")

    assert analysis.complexity_score == 0.0
    assert analysis.functions == []

def test_generate_tests_for_function(generator):
    """Test generating test cases for a function."""
    analysis = generator.analyze_code(SAMPLE_CODE, "test_file.py")
    func_info = analysis.functions[0]

    tests = generator.generate_tests_for_function(func_info, "test_file.py")

    assert len(tests) > 0
    assert all(isinstance(t, TestCase) for t in tests)

    # Check types of tests generated
    types = [t.test_type for t in tests]
    assert TestType.UNIT in types

    # Check logic of generated happy path
    happy_path = next(t for t in tests if "happy_path" in t.test_name)
    assert "calculate_area" in happy_path.test_code
    assert "assert" in happy_path.test_code

def test_smart_selector():
    """Test selecting high priority tests."""
    selector = SmartTestSelector()

    test1 = TestCase(
        test_id="t1", test_name="critical_test", test_type=TestType.SECURITY,
        description="", function_under_test="auth", test_code="", expected_outcome="",
        input_values={}, edge_cases_covered=[], confidence=0.9, priority=10,
        estimated_execution_time=1.0
    )

    test2 = TestCase(
        test_id="t2", test_name="minor_test", test_type=TestType.UNIT,
        description="", function_under_test="util", test_code="", expected_outcome="",
        input_values={}, edge_cases_covered=[], confidence=0.5, priority=1,
        estimated_execution_time=1.0
    )

    # Simulate that "auth" was changed
    selected = selector.select_tests([test1, test2], changed_files=["auth.py"], time_budget=10.0)

    assert len(selected) == 2
    assert selected[0] == test1 # Higher priority should be first

def test_coverage_optimizer():
    """Test coverage optimization logic."""
    optimizer = CoverageOptimizer()

    test1 = TestCase(
        test_id="t1", test_name="big_test", test_type=TestType.UNIT,
        description="", function_under_test="big", test_code="", expected_outcome="",
        input_values={}, edge_cases_covered=[], confidence=1.0, priority=5,
        estimated_execution_time=1.0
    )

    test2 = TestCase(
        test_id="t2", test_name="small_test", test_type=TestType.UNIT,
        description="", function_under_test="small", test_code="", expected_outcome="",
        input_values={}, edge_cases_covered=[], confidence=0.1, priority=5,
        estimated_execution_time=1.0
    )

    # Should pick test1 because it simulates higher coverage (based on confidence)
    optimized = optimizer.optimize_test_suite([test1, test2], coverage_goal=10.0)

    assert len(optimized) > 0
    assert test1 in optimized
