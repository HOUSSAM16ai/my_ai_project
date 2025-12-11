from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class TestType(Enum):
    """أنواع الاختبارات"""

    UNIT = "unit"
    INTEGRATION = "integration"
    E2E = "end_to_end"
    PERFORMANCE = "performance"
    SECURITY = "security"
    MUTATION = "mutation"


class CoverageType(Enum):
    """أنواع التغطية"""

    LINE = "line"
    BRANCH = "branch"
    FUNCTION = "function"
    CONDITION = "condition"
    PATH = "path"


@dataclass
class TestCase:
    """حالة اختبار مولدة بالذكاء الاصطناعي"""

    test_id: str
    test_name: str
    test_type: TestType
    description: str
    function_under_test: str
    test_code: str
    expected_outcome: str
    input_values: dict[str, Any]
    edge_cases_covered: list[str]
    confidence: float  # 0-1
    priority: int  # 1-10
    estimated_execution_time: float  # seconds
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "test_id": self.test_id,
            "test_name": self.test_name,
            "test_type": self.test_type.value,
            "description": self.description,
            "function_under_test": self.function_under_test,
            "test_code": self.test_code,
            "expected_outcome": self.expected_outcome,
            "input_values": self.input_values,
            "edge_cases_covered": self.edge_cases_covered,
            "confidence": self.confidence,
            "priority": self.priority,
            "estimated_execution_time": self.estimated_execution_time,
        }


@dataclass
class CodeAnalysis:
    """تحليل الكود لتوليد الاختبارات"""

    file_path: str
    functions: list[dict[str, Any]]
    classes: list[dict[str, Any]]
    complexity_score: float
    dependencies: list[str]
    edge_cases: list[str]
    security_risks: list[str]
