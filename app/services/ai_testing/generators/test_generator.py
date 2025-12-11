import ast
from collections import defaultdict
from typing import Any

from app.services.ai_testing.domain.models import CodeAnalysis, TestCase, TestType


class AITestGenerator:
    """
    مولد اختبارات ذكي يستخدم AI لتوليد حالات اختبار شاملة
    """

    def __init__(self):
        self.generated_tests: dict[str, list[TestCase]] = defaultdict(list)
        self.coverage_data: dict[str, dict[str, float]] = defaultdict(dict)

    def analyze_code(self, code: str, file_path: str) -> CodeAnalysis:
        """
        تحليل الكود لاستخراج المعلومات اللازمة لتوليد الاختبارات
        """
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return CodeAnalysis(
                file_path=file_path,
                functions=[],
                classes=[],
                complexity_score=0.0,
                dependencies=[],
                edge_cases=[],
                security_risks=[],
            )

        functions = []
        classes = []
        dependencies = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Analyze function
                func_info = self._analyze_function(node)
                functions.append(func_info)

            elif isinstance(node, ast.ClassDef):
                # Analyze class
                class_info = self._analyze_class(node)
                classes.append(class_info)

            elif isinstance(node, ast.Import):
                # Track dependencies
                for alias in node.names:
                    dependencies.append(alias.name)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    dependencies.append(node.module)

        # Calculate complexity
        complexity_score = self._calculate_complexity(tree)

        # Identify edge cases
        edge_cases = self._identify_edge_cases(functions)

        # Identify security risks
        security_risks = self._identify_security_risks(tree)

        return CodeAnalysis(
            file_path=file_path,
            functions=functions,
            classes=classes,
            complexity_score=complexity_score,
            dependencies=list(set(dependencies)),
            edge_cases=edge_cases,
            security_risks=security_risks,
        )

    def _analyze_function(self, node: ast.FunctionDef) -> dict[str, Any]:
        """تحليل function محدد"""
        # Extract parameters
        params = []
        for arg in node.args.args:
            param_info = {
                "name": arg.arg,
                "annotation": ast.unparse(arg.annotation) if arg.annotation else None,
            }
            params.append(param_info)

        # Extract return type
        return_type = ast.unparse(node.returns) if node.returns else None

        # Count lines
        lines = len([n for n in ast.walk(node) if isinstance(n, ast.stmt)])

        # Find branches (if/else, try/except, etc.)
        branches = len([n for n in ast.walk(node) if isinstance(n, ast.If | ast.While | ast.For)])

        return {
            "name": node.name,
            "params": params,
            "return_type": return_type,
            "lines": lines,
            "branches": branches,
            "complexity": branches + 1,  # Cyclomatic complexity approximation
            "docstring": ast.get_docstring(node),
        }

    def _analyze_class(self, node: ast.ClassDef) -> dict[str, Any]:
        """تحليل class محدد"""
        methods = []
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append(self._analyze_function(item))

        return {
            "name": node.name,
            "methods": methods,
            "bases": [ast.unparse(base) for base in node.bases],
            "docstring": ast.get_docstring(node),
        }

    def _calculate_complexity(self, tree: ast.AST) -> float:
        """حساب تعقيد الكود"""
        # Count decision points
        decision_points = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.If | ast.While | ast.For | ast.ExceptHandler):
                decision_points += 1
            elif isinstance(node, ast.BoolOp):
                decision_points += len(node.values) - 1

        # Normalize to 0-100 scale
        return min(100, decision_points * 5)

    def _identify_edge_cases(self, functions: list[dict[str, Any]]) -> list[str]:
        """تحديد الحالات الحدية المحتملة"""
        edge_cases = []

        for func in functions:
            # Check for numeric parameters
            for param in func["params"]:
                if param["annotation"] and "int" in param["annotation"].lower():
                    edge_cases.append(f"{func['name']}: Test with 0, negative, max int")
                if param["annotation"] and "float" in param["annotation"].lower():
                    edge_cases.append(f"{func['name']}: Test with 0.0, negative, infinity, NaN")
                if param["annotation"] and "str" in param["annotation"].lower():
                    edge_cases.append(
                        f"{func['name']}: Test with empty string, very long string, special chars"
                    )
                if param["annotation"] and "list" in param["annotation"].lower():
                    edge_cases.append(
                        f"{func['name']}: Test with empty list, single item, many items"
                    )
                if param["annotation"] and "dict" in param["annotation"].lower():
                    edge_cases.append(f"{func['name']}: Test with empty dict, nested dict")

        return edge_cases

    def _identify_security_risks(self, tree: ast.AST) -> list[str]:
        """تحديد المخاطر الأمنية المحتملة"""
        risks = []

        for node in ast.walk(tree):
            # Check for eval/exec usage
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ["eval", "exec"]:
                    risks.append("Dangerous: Use of eval/exec detected")
                elif node.func.id == "open":
                    risks.append("File I/O: Verify file path validation")

            # Check for SQL-like strings
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
                and any(
                    kw in node.value.lower() for kw in ["select ", "insert ", "update ", "delete "]
                )
            ):
                risks.append("SQL Injection Risk: Raw SQL query detected")

        return risks

    def generate_tests_for_function(
        self, func_info: dict[str, Any], file_path: str, num_tests: int = 5
    ) -> list[TestCase]:
        """
        توليد حالات اختبار لـ function محدد
        """
        tests: list[TestCase] = []
        func_name = func_info["name"]

        # Generate happy path test
        test = self._generate_happy_path_test(func_info, file_path)
        if test:
            tests.append(test)

        # Generate edge case tests
        edge_tests = self._generate_edge_case_tests(func_info, file_path)
        tests.extend(edge_tests)

        # Generate error case tests
        error_tests = self._generate_error_case_tests(func_info, file_path)
        tests.extend(error_tests)

        # Generate boundary tests
        boundary_tests = self._generate_boundary_tests(func_info, file_path)
        tests.extend(boundary_tests)

        # Limit to requested number
        tests = tests[:num_tests]

        # Store generated tests
        self.generated_tests[func_name].extend(tests)

        return tests

    def _generate_happy_path_test(
        self, func_info: dict[str, Any], file_path: str
    ) -> TestCase | None:
        """توليد اختبار الحالة السعيدة"""
        func_name = func_info["name"]
        params = func_info["params"]

        # Generate sample inputs
        inputs = {}
        for param in params:
            if param["name"] == "self":
                continue
            inputs[param["name"]] = self._generate_sample_value(param)

        # Generate test code
        test_code = f"""def test_{func_name}_happy_path():
    \"\"\"Test {func_name} with valid inputs\"\"\"
    # Arrange
    {self._format_inputs(inputs)}

    # Act
    result = {func_name}({", ".join(f"{k}={k}" for k in inputs)})

    # Assert
    assert result is not None
    # Add more specific assertions based on expected behavior
"""

        return TestCase(
            test_id=f"test_{func_name}_001",
            test_name=f"test_{func_name}_happy_path",
            test_type=TestType.UNIT,
            description=f"Test {func_name} with valid inputs",
            function_under_test=func_name,
            test_code=test_code,
            expected_outcome="Success with valid output",
            input_values=inputs,
            edge_cases_covered=["happy_path"],
            confidence=0.9,
            priority=8,
            estimated_execution_time=0.01,
        )

    def _generate_edge_case_tests(
        self, func_info: dict[str, Any], file_path: str
    ) -> list[TestCase]:
        """توليد اختبارات الحالات الحدية"""
        tests: list[TestCase] = []
        func_name = func_info["name"]
        params = func_info["params"]

        edge_values: dict[str, list[Any]] = {
            "int": [0, -1, 1, 999999, -999999],
            "float": [0.0, -1.0, 1.0, float("inf"), float("-inf")],
            "str": ["", "a", "very long string" * 100, "特殊字符", '<script>alert("xss")</script>'],
            "list": [[], [1], list(range(1000))],
            "dict": [{}, {"key": "value"}, {"nested": {"key": "value"}}],
            "bool": [True, False],
        }

        for param in params:
            if param["name"] == "self":
                continue

            param_type = self._infer_type(param)
            if param_type in edge_values:
                edge_values_list = edge_values[param_type]
                for edge_val in edge_values_list[:2]:  # Limit to 2 per param
                    inputs = {param["name"]: edge_val}

                    test_code = f"""def test_{func_name}_edge_{param["name"]}_{edge_val}():
    \"\"\"Test {func_name} with edge case: {param["name"]}={edge_val}\"\"\"
    # Arrange
    {param["name"]} = {edge_val!r}

    # Act & Assert
    try:
        result = {func_name}({param["name"]}={param["name"]})
        assert result is not None
    except Exception as e:
        # Document expected exceptions
        assert isinstance(e, ValueError | TypeError)
"""

                    tests.append(
                        TestCase(
                            test_id=f"test_{func_name}_{len(tests) + 1:03d}",
                            test_name=f"test_{func_name}_edge_{param['name']}",
                            test_type=TestType.UNIT,
                            description=f"Test {func_name} with edge case: {param['name']}={edge_val}",
                            function_under_test=func_name,
                            test_code=test_code,
                            expected_outcome="Handles edge case gracefully",
                            input_values=inputs,
                            edge_cases_covered=[f"edge_{param['name']}"],
                            confidence=0.8,
                            priority=7,
                            estimated_execution_time=0.01,
                        )
                    )

        return tests

    def _generate_error_case_tests(
        self, func_info: dict[str, Any], file_path: str
    ) -> list[TestCase]:
        """توليد اختبارات حالات الخطأ"""
        tests: list[TestCase] = []
        func_name = func_info["name"]
        params = func_info["params"]

        # Test with None values
        for param in params:
            if param["name"] == "self":
                continue

            test_code = f"""def test_{func_name}_none_{param["name"]}():
    \"\"\"Test {func_name} with None for {param["name"]}\"\"\"
    # Act & Assert
    with pytest.raises((ValueError, TypeError)):
        {func_name}({param["name"]}=None)
"""

            tests.append(
                TestCase(
                    test_id=f"test_{func_name}_error_{len(tests) + 1:03d}",
                    test_name=f"test_{func_name}_none_{param['name']}",
                    test_type=TestType.UNIT,
                    description=f"Test {func_name} rejects None for {param['name']}",
                    function_under_test=func_name,
                    test_code=test_code,
                    expected_outcome="Raises appropriate exception",
                    input_values={param["name"]: None},
                    edge_cases_covered=["null_handling"],
                    confidence=0.85,
                    priority=6,
                    estimated_execution_time=0.01,
                )
            )

        return tests[:3]  # Limit error tests

    def _generate_boundary_tests(self, func_info: dict[str, Any], file_path: str) -> list[TestCase]:
        """توليد اختبارات الحدود"""
        tests: list[TestCase] = []
        # Would implement boundary value analysis here
        return tests

    def _generate_sample_value(self, param: dict[str, Any]) -> Any:
        """توليد قيمة عينة لـ parameter"""
        param_type = self._infer_type(param)

        samples = {
            "int": 42,
            "float": 3.14,
            "str": "test_value",
            "list": [1, 2, 3],
            "dict": {"key": "value"},
            "bool": True,
        }

        return samples.get(param_type, "default_value")

    def _infer_type(self, param: dict[str, Any]) -> str:
        """استنتاج نوع parameter"""
        if param["annotation"]:
            annotation = param["annotation"].lower()
            for type_name in ["int", "float", "str", "list", "dict", "bool"]:
                if type_name in annotation:
                    return type_name
        return "any"

    def _format_inputs(self, inputs: dict[str, Any]) -> str:
        """تنسيق inputs للكود"""
        lines = []
        for key, value in inputs.items():
            lines.append(f"    {key} = {value!r}")
        return "\n".join(lines)
