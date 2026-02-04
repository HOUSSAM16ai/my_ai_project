"""
اختبار إظهار سلم التنقيط حتى عند طلب سؤال محدد.
"""

from app.services.chat.graph.components.context_composer import FirewallContextComposer
from app.services.chat.graph.domain import WriterIntent


def test_context_composer_keeps_grading_for_requested_segment() -> None:
    composer = FirewallContextComposer()
    search_results = [
        {
            "type": "exercise",
            "content": (
                "# السؤال الأول\n"
                "نص التمرين هنا.\n\n"
                "[grading: ex_1]\n"
                "**سلم التنقيط**\n"
                "- بند 1: 1 نقطة\n"
            ),
        }
    ]

    rendered = composer.compose(
        search_results=search_results,
        intent=WriterIntent.GRADING_REQUEST,
        user_message="أريد سلم التنقيط للسؤال الأول",
    )

    assert "سلم التنقيط" in rendered
