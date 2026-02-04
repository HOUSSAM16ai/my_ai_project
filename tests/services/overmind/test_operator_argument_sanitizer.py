"""
اختبارات تنقية وسائط البحث التعليمي داخل المنفذ.
"""

from app.services.overmind.agents.operator import OperatorAgent
from app.services.overmind.domain.context import InMemoryCollaborationContext


def test_prepare_search_educational_args_merges_context():
    operator = OperatorAgent(task_executor=type("Dummy", (), {})())
    context = InMemoryCollaborationContext(
        {"objective": "طلب تمرين", "exercise_metadata": {"year": "2024"}}
    )

    prepared = operator._prepare_search_educational_args(  # noqa: SLF001
        {"limit": 5, "q": "تمرين الاحتمالات", "year": "2023"}, context
    )

    assert prepared["query"] == "تمرين الاحتمالات"
    assert prepared["year"] == "2023"
    assert "limit" not in prepared
