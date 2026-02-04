"""
اختبارات البحث المحلي عند توفر بيانات وصفية بدون واجهة YAML.
"""

from app.services.chat.tools.retrieval import local_store


def test_local_store_matches_inline_metadata_subject_branch():
    content = local_store.search_local_knowledge_base(
        query="تمرين الاحتمالات",
        year="2024",
        subject="رياضيات",
        branch="علوم تجريبية",
        exam_ref="الموضوع الأول",
    )

    assert "التمرين الأول" in content
