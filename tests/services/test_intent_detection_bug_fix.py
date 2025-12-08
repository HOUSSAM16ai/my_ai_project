
import pytest
from app.services.chat.intent import IntentDetector, ChatIntent

def test_deep_analysis_intent_keywords():
    """
    Verifies that the new deep analysis intent detection works for common Arabic and English phrases.
    """

    # English Cases
    assert IntentDetector.detect("explain the architecture").intent == ChatIntent.DEEP_ANALYSIS
    assert IntentDetector.detect("what is the purpose of this module").intent == ChatIntent.DEEP_ANALYSIS
    assert IntentDetector.detect("analyze the code quality").intent == ChatIntent.DEEP_ANALYSIS
    assert IntentDetector.detect("how can we improve performance").intent == ChatIntent.DEEP_ANALYSIS
    assert IntentDetector.detect("find bugs in this file").intent == ChatIntent.DEEP_ANALYSIS
    assert IntentDetector.detect("list the dependencies").intent == ChatIntent.DEEP_ANALYSIS

    # Arabic Cases
    assert IntentDetector.detect("اشرح بنية النظام").intent == ChatIntent.DEEP_ANALYSIS
    assert IntentDetector.detect("ما هو الغرض من هذه الوظيفة").intent == ChatIntent.DEEP_ANALYSIS
    assert IntentDetector.detect("حلل الكود").intent == ChatIntent.DEEP_ANALYSIS
    assert IntentDetector.detect("كيف يمكن تحسين الأداء").intent == ChatIntent.DEEP_ANALYSIS
    assert IntentDetector.detect("ما هي المشاكل في هذا الملف").intent == ChatIntent.DEEP_ANALYSIS

def test_deep_analysis_intent_false_positives():
    """
    Verifies that simple chat messages are NOT classified as deep analysis.
    """
    assert IntentDetector.detect("hello").intent == ChatIntent.SIMPLE_CHAT
    assert IntentDetector.detect("how are you?").intent == ChatIntent.SIMPLE_CHAT
    assert IntentDetector.detect("write a python script").intent != ChatIntent.DEEP_ANALYSIS
    assert IntentDetector.detect("read file main.py").intent == ChatIntent.FILE_READ
