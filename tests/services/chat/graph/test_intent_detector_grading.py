"""
اختبارات نية طلب سلم التنقيط في كاشف النية.
"""

from app.services.chat.graph.components.intent_detector import RegexIntentDetector
from app.services.chat.graph.domain import WriterIntent


def test_grading_request_intent():
    detector = RegexIntentDetector()
    intent = detector.analyze("أريد سلم التنقيط مع الحل النموذجي")

    assert intent == WriterIntent.GRADING_REQUEST
