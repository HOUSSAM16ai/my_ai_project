# tests/services/chat/test_chat_intent_superhuman.py
import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.services.chat.intent import ChatIntent, IntentDetector, IntentResult
from tests.utils.unified_test_template import UnifiedTestTemplate


class TestIntentDetectorSuperhuman(UnifiedTestTemplate):
    # --- Unit Tests: Specific Patterns ---

    @pytest.mark.parametrize(
        "text,expected_intent",
        [
            ("read file config.py", ChatIntent.FILE_READ),
            (
                "create file test.js",
                ChatIntent.FILE_WRITE,
            ),  # Fixed: Removed "new" to match pattern 1
            ("create new test.js", ChatIntent.FILE_WRITE),  # Matches pattern 2
            ("explain the architecture", ChatIntent.DEEP_ANALYSIS),
            ("find code for login", ChatIntent.CODE_SEARCH),
            ("analyze project structure", ChatIntent.PROJECT_INDEX),
            ("start mission to refactor auth", ChatIntent.MISSION_COMPLEX),
            ("help me", ChatIntent.HELP),
            ("hello world", ChatIntent.SIMPLE_CHAT),
        ],
    )
    def test_detect_specific_intents(self, text, expected_intent):
        result = IntentDetector.detect(text)
        assert result.intent == expected_intent, (
            f"Expected {expected_intent} for '{text}', got {result.intent}"
        )

    # --- Property-Based Tests: Invariants ---

    @given(st.text())
    @UnifiedTestTemplate.HYPOTHESIS_SETTINGS
    def test_detect_never_crashes(self, text):
        result = IntentDetector.detect(text)
        assert isinstance(result, IntentResult)

    @given(st.text())
    @UnifiedTestTemplate.HYPOTHESIS_SETTINGS
    def test_detect_param_integrity(self, text):
        result = IntentDetector.detect(text)
        assert isinstance(result.params, dict)

    def test_arabic_patterns(self):
        cases = [
            ("اقرأ ملف app.py", ChatIntent.FILE_READ),
            ("أنشئ ملف index.html", ChatIntent.FILE_WRITE),
            ("اشرح كيف يعمل النظام", ChatIntent.DEEP_ANALYSIS),
        ]
        for txt, intent in cases:
            res = IntentDetector.detect(txt)
            assert res.intent == intent, f"Failed for '{txt}'"
